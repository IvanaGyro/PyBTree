import random
from collections import OrderedDict
from btree import Pair, BTree


def test(pairs=None):
    try:
        error_info = OrderedDict()
        if pairs is not None:
            pair_cnt = len(pairs)
            seq = pairs
            b_tree = BTree(pairs)
            error_info['Insert sequence'] = seq
            error_info['Tree'] = b_tree
        else:
            pair_cnt = 200
            seq = []
            b_tree = BTree()
            error_info['Insert sequence'] = seq
            error_info['Tree'] = b_tree
            for i in range(pair_cnt):
                pair = Pair(random.randint(1, 50), random.randint(1, 1000))
                seq.append(pair)
                b_tree.insert(pair)
                assert b_tree.is_valid(), \
                    'Occur the error when inserting the pair.'

        sorted_seq = sorted(seq)
        tree_seq = [pair for pair in b_tree]
        error_info['Sorted insert sequence'] = sorted_seq
        error_info['Output sequence'] = tree_seq
        assert len(sorted_seq) == len(tree_seq), \
            'The length of the output sequence of the tree i not correct.'
        for i in range(len(sorted_seq)):
            assert id(sorted_seq[i]) == id(tree_seq[i]), \
                'Input node and output nodes are not the same.'

        del_seq = []
        error_info['Delete sequence'] = del_seq
        for_del = seq.copy()
        for i in range(pair_cnt): # delete until zero node in the tree
            idx = random.randint(0, len(for_del)-1)
            pair = for_del.pop(idx)
            del_seq.append(pair)
            b_tree.delete_one(pair)
            assert b_tree.is_valid(), f'Deleting fails. Pair:{pair}'
        return True
    except Exception as e:
        extra_msg = '\n\n'.join([f'{k}:\n{v}' for k, v in error_info.items()])
        # The error message may be at the first item?
        e.args = (e.args[0] + f'\n{extra_msg}', *e.args[1:])
        raise e

# helper function
def str2pairs(s):
    return [Pair(k, v) for p in s for k, v in p.items()]   

# if __name__ == '__main__':
#     for i in range(10):
#         test()
#     print('Pass the tests!')
