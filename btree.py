from __future__ import annotations
from typing import Iterable, Optional, Union, List
import bisect
from collections.abc import MutableSequence
from collections import Counter

from abc import ABCMeta, abstractmethod
from typing import Any, TypeVar

'''
Definition of a Comparable type
link: https://www.python.org/dev/peps/pep-0484/#type-variables-with-an-upper-bound
'''
class Comparable(metaclass=ABCMeta):
    @abstractmethod
    def __lt__(self, other: Any) -> bool: ...

CT = TypeVar('CT', bound=Comparable)


class Pair:

    __slots__ = ('key', 'val',)

    def __init__(self, key, val=None):
        self.key = key
        self.val = val

    def __eq__(self, other):
        return self.key == other

    def __ne__(self, other):
        return self.key != other

    def __lt__(self, other):
        return self.key < other

    def __gt__(self, other):
        return self.key > other

    def __le__(self, other):
        return self.key <= other

    def __ge__(self, other):
        return self.key >= other

    def __str__(self):
        return f'{{{self.key}: {self.val}}}'

    def __repr__(self):
        return self.__str__()


class PairList(Pair, MutableSequence):

    __slots__ = ('pairs',)

    def __init__(self, key, pairs: List[Pair]):
        if len(pairs) < 2:
            raise ValueError
        super().__init__(key, pairs)
        self.pairs = self.val

    def __getitem__(self, *args, **kwargs):
        return self.pairs.__getitem__(*args, **kwargs)
    
    def __len__(self, *args, **kwargs):
        return self.pairs.__len__(*args, **kwargs)
    
    def __setitem__(self, *args, **kwargs):
        return self.pairs.__setitem__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        return self.pairs.__delitem__(*args, **kwargs)
    
    def __str__(self):
        return f'{{{self.key}: {[pair.val for pair in self.pairs]}}}'

    def insert(self, *args, **kwargs):
        return self.pairs.insert(*args, **kwargs)

    def is_valid(self):
        return len(self.pairs) == len(
            pair for pair in self.pairs if pair.key == self.key)
    

class Node:

    __slots__ = ('__degree', '__max_pairs', '__min_pairs', 'pairs', 'children')

    def __init__(
        self,
        degree,
        pairs: Optional[List[Pair]] = None,
        children: Optional[List[Union[None, Node]]] = None,
    ):
        self.__degree = degree
        self.__max_pairs = (degree << 1) - 1
        self.__min_pairs = degree - 1

        if pairs is None:
            self.pairs = []
        else:
            self.pairs = pairs

        if children is None:
            self.children = [None]
        else:
            self.children = children
            cnt = Counter(self.children)[None]
            if cnt != len(self.children) and cnt != 0:
                raise ValueError
        if len(self.children) - len(self.pairs) != 1:
            raise ValueError

    def __len__(self):
        return len(self.pairs)

    def __str__(self):
        return str(self.pairs)

    def __repr__(self):
        return self.__str__()

    def index(self, pair: Pair):
        idx = bisect.bisect_left(self.pairs, pair)
        if idx == len(self.pairs) or self.pairs[idx] != pair:
            return idx, None
        else:
            return idx, self.pairs[idx]
    
    def split_child(self, index):
        # The child that is split will be put at the right side
        right = self.children[index]

        # get the middle pair
        mid = right.__max_pairs >> 1
        mid_pair = right.pairs[mid]

        # split
        left = Node(right.__degree, right.pairs[:mid], right.children[:mid+1])
        right.pairs = right.pairs[mid+1:]
        right.children = right.children[mid+1:]

        # link the parent and the children
        self.pairs.insert(index, mid_pair)
        self.children.insert(index, left)
        self.children[index + 1] = right

    def merge_children(self, index) -> Pair:
        '''merge the left child and the right child of self.pairs[index]'''
        left_child = self.children[index]
        right_child = self.children[index + 1]

        # merge all pairs into the left child  
        left_child.pairs.append(self.pairs[index])
        left_child.pairs += right_child.pairs
        left_child.children += right_child.children

        self.pairs.pop(index)
        self.children.pop(index+1)

        return left_child

    @property
    def is_leaf(self):
        # For this implementation, if a node is not the leaf, all of its 
        # children must not be None
        return self.children[0] is None

    @property
    def is_full(self):
        return len(self.pairs) == self.__max_pairs


class BTree:
    def __init__(self, pairs: Optional[Iterable[Pair]] = None, degree=3):
        self.__node_max_pair = degree * 2 - 1
        self.__node_min_pair = degree - 1
        self.__degree = degree
        self.root = self.new_node()
        if pairs:
            for pair in pairs:
                self.insert(pair)

    def __str__(self):
        queue = []
        res = []
        queue.append((0, [], self.root))
        last_layer = 0
        while queue:
            layer, path, node = queue.pop(0)
            if last_layer != layer:
                res.append('|')
                last_layer = layer
            res.append(f'{layer}: ({", ".join(map(lambda p: str(p), path))}): {str(node)}')
            if not node.is_leaf:
                for i in range(len(node.children)):
                    queue.append((layer + 1, path + [i], node.children[i]))
        return '\n'.join(res)

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        def yield_pair(pair):
            if isinstance(pair, PairList):
                yield from pair
            else:
                yield pair

        def dfs(node):
            for i in range(len(node)):
                if not node.is_leaf:
                    yield from dfs(node.children[i])
                yield from yield_pair(node.pairs[i])
            if not node.is_leaf:
                yield from dfs(node.children[len(node)])
                
        return dfs(self.root)
        
    def new_node(self, pairs=None, children=None):
        return Node(self.__degree, pairs, children)

    def _find_insert(self, key: Union[Pair, CT]):
        if self.root.is_full:
            # split root
            new_root = self.new_node()
            new_root.children[0] = self.root
            self.root = new_root
            self.root.split_child(0)

        cur_node = self.root
        while True:
            index, target = cur_node.index(key)
            if target is not None or cur_node.is_leaf:
                return cur_node, index
            if cur_node.children[index].is_full:
                cur_node.split_child(index)
            else:               
                cur_node = cur_node.children[index]

    def _find(self, key):
        cur_node = self.root
        tmp_pair = Pair(key)
        while True:
            idx, target = cur_node.index(tmp_pair)
            if target is not None:
                return target 
            if cur_node.children[idx] is None:
                return None
            cur_node = cur_node.children[idx]
    
    def search_all(self, key, value_only=True):
        match = self._find(key)
        if match is None:
            return None
        if not isinstance(match, PairList):
            match = [match]
        else:
            match = match.pairs

        if value_only:
            return [pair.val for pair in match]
        else:
            return match
                
    def insert(self, pair: Pair):    
        node, index = self._find_insert(pair)
        if index < len(node.pairs) and node.pairs[index].key == pair.key:
            successor = node.pairs[index]
            if isinstance(successor, PairList):
                successor.append(pair)
            else:
                node.pairs[index] = PairList(successor.key, [successor, pair])
        else:
            node.pairs.insert(index, pair)
            node.children.insert(index, None)
        return
            
    def _delete(self, node: Node, pair: Pair, ignore_id=False):
        idx, target = node.index(pair)

        if not ignore_id:
            if isinstance(target, PairList):
                found = False
                for i in range(len(target)):
                    if id(target[i]) == id(pair):
                        target.pop(i)
                        found = True
                        break
                if not found:
                    raise ValueError
                if len(target) <= 1:
                    node.pairs[idx], = target
                return
            if target is not None:
                if id(target) != id(pair):
                    raise ValueError
            
        if target is not None:
            if node.is_leaf:
                node.pairs.pop(idx)
                node.children.pop(idx)
                return
            
            left_child = node.children[idx]
            right_child = node.children[idx+1]
            if len(left_child) > self.__node_min_pair:
                ptr = left_child
                while not ptr.is_leaf:
                    ptr = ptr.children[-1]
                predecessor = ptr.pairs[-1]
                self._delete(left_child, predecessor, ignore_id=True)
                node.pairs[idx] = predecessor
                return
            elif len(right_child) > self.__node_min_pair:
                ptr = right_child
                while not ptr.is_leaf:
                    ptr = ptr.children[0]
                successor = ptr.pairs[0]
                self._delete(right_child, successor, ignore_id=True)
                node.pairs[idx] = successor
                return
            else:
                node.merge_children(idx)
                self._delete(left_child, pair, ignore_id=True)
                return
        else:
            next_child = node.children[idx]
            if len(next_child) <= self.__node_min_pair:
                go_next = False
                if idx >= 1:
                    left_sibling = node.children[idx-1]
                    if len(left_sibling) > self.__node_min_pair:
                        next_child.pairs.insert(0, node.pairs[idx-1])
                        next_child.children.insert(0, left_sibling.children.pop())
                        node.pairs[idx-1] = left_sibling.pairs.pop()
                        go_next = True
                if idx < len(node) and not go_next:
                    right_sibling = node.children[idx+1]
                    if len(right_sibling) > self.__node_min_pair:
                        next_child.pairs.append(node.pairs[idx])
                        next_child.children.append(right_sibling.children.pop(0))
                        node.pairs[idx] = right_sibling.pairs.pop(0)
                        go_next = True
                if not go_next:
                    if idx < len(node):
                        next_child = node.merge_children(idx)
                    elif idx >= 1:
                        next_child = node.merge_children(idx - 1)
            self._delete(next_child, pair, ignore_id)
                        
    def _kick_off_root(self):
        if len(self.root) == 0 and not self.root.is_leaf:
            self.root = self.root.children[0]

    def delete_one(self, pair: Pair):
        self._delete(self.root, pair, ignore_id=False)
        self._kick_off_root()

    def delete(self, key):
        pair = Pair(key)
        self._delete(self.root, pair, ignore_id=True)
        self._kick_off_root()

    def is_valid(self):
        def check_node(node, low, high):
            # empty tree
            if node == self.root and len(node) == 0:
                return True
            
            # check the length of pairs and children
            if node != self.root and len(node) < self.__node_min_pair:
                return False
            if len(node) > self.__node_max_pair:
                return False
            if len(node.children) - len(node) != 1:
                return False
            
            # If a node is a leaf, all of its children must be None. On the
            # other hand, if a node is not a leaf, all of its children must
            # not be None.
            none_cnt = Counter(node.children)[None]
            if not node.is_leaf and none_cnt != 0:
                return False
            if node.is_leaf and none_cnt != len(node) + 1:
                return False
            
            # check the pairs are sorted
            last_pair = node.pairs[0]
            if low is not None and last_pair <= low:
                return False
            for i in range(1, len(node)):
                if node.pairs[i] < last_pair:
                    return False
                last_pair = node.pairs[i]
            if high is not None and last_pair >= high:
                return False
            
            # check other nodes with DFS
            if not node.is_leaf:
                tmp_pairs = [low, *node.pairs, high]
                for i in range(len(node) + 1):
                    if not check_node(node.children[i], tmp_pairs[i], tmp_pairs[i+1]):
                        return False
            return True
            
        return check_node(self.root, None, None)
