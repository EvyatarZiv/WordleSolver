from string import ascii_lowercase
from random import randint, seed
from time import time_ns
from typing import Optional
from math import ceil, log2, floor


class LetterControl:
    _control_blocks = {}

    def __init__(self, letter: str, word_len: int):
        assert letter in ascii_lowercase
        self.letter: str = letter
        self._false_positions: set[int] = set()
        self._true_positions: set[int] = set()
        self._min_count: int = 0
        self._at_large: bool = False
        self._max_count: int = word_len
        self._word_len: int = word_len

    def is_legal(self, position: int, prefix: str) -> bool:
        req_count = 0
        for c in ascii_lowercase:
            req_count += max(LetterControl._control_blocks[c]._min_count - prefix.count(c), 0)
            if c == self.letter and LetterControl._control_blocks[c]._min_count - prefix.count(c) > 0:
                req_count -= 1
        return (position not in self._false_positions) and (prefix.count(self.letter) < self._max_count) and (
                req_count < self._word_len - position)

    def mark_illegal_position(self, position: int, other_implied: bool = False) -> None:
        if position in self._true_positions or position in self._false_positions:
            return None
        self._false_positions.add(position)
        self._max_count -= 1
        if other_implied and not self._at_large:
            self._at_large = True
            self._min_count += 1
        return None

    def mark_legal_position(self, position: int):
        if position in self._true_positions:
            return None
        if position in self._false_positions:
            self._false_positions.remove(position)
            self._max_count += 1
        self._true_positions.add(position)
        if self._at_large:
            self._at_large = False
        else:
            self._min_count += 1
        return None

    @staticmethod
    def make_letter_ctrl(letter: str, word_len: int) -> None:
        LetterControl._control_blocks[letter] = LetterControl(letter, word_len)

    @staticmethod
    def get_letter_ctrl(letter: str) -> 'LetterControl':
        if letter not in LetterControl._control_blocks.keys():
            print(f'Letter not in keys: {letter}')
        assert letter in LetterControl._control_blocks.keys()
        return LetterControl._control_blocks[letter]


class TreeNode:
    def __init__(self, position: int, prefix: str = "", control_block: LetterControl = None):
        self.ctrl_block: LetterControl = control_block
        self.idx: int = position
        self.prefix = prefix
        self.children: dict = {}
        self.subtree_size = 0
        self.is_leaf: bool = False

    def add_children(self, suffix_list: list[str], word_len: int) -> None:
        suffix_dict = {c: set() for c in ascii_lowercase}
        for suf in suffix_list:
            if suf[0] not in self.children.keys():
                self.children[suf[0]] = TreeNode(control_block=LetterControl.get_letter_ctrl(suf[0]),
                                                 position=self.idx + 1, prefix=self.prefix + (
                        self.ctrl_block.letter if self.ctrl_block is not None else ""))
            if len(suf) > 1:
                suffix_dict[suf[0]].add(suf[1:])
        for c in suffix_dict.keys():
            if len(suffix_dict[c]) > 0:
                self.children[c].add_children(suffix_list=list(suffix_dict[c]), word_len=word_len)
                self.subtree_size += self.children[c].subtree_size
            elif c in self.children.keys():
                self.children[c].is_leaf = True
                self.subtree_size += 1
        return None

    def purge_inactive(self) -> None:
        self.subtree_size = 0
        if not self.is_active():
            return None
        for c in list(self.children.keys()):
            self.children[c].purge_inactive()
            if self.children[c].subtree_size == 0 and not (self.children[c].is_leaf and self.children[c].is_active()):
                del self.children[c]
            else:
                self.subtree_size += self.children[c].subtree_size + self.children[c].is_leaf
        if self.ctrl_block is not None:
            WordTree.freq_dict[self.ctrl_block.letter] += self.subtree_size + self.is_leaf
        return None

    def is_active(self) -> bool:
        return self.ctrl_block is None or self.ctrl_block.is_legal(position=self.idx, prefix=self.prefix)

    def select_random_trail(self) -> str:
        if self.is_leaf:
            return ""
        next_char: str = list(self.children.keys())[randint(0, len(self.children.keys()))]
        return next_char + self.children[next_char].select_random_trail()

    def select_with_tree_priority(self) -> str:
        if self.is_leaf:
            return ""
        prio = WordTree.get_tree_priority()
        act = list(self.children.keys())
        if randint(0, 9) != 0:
            currfix = self.prefix if self.ctrl_block is None else self.prefix + self.ctrl_block.letter
            tmp = list(filter(lambda x: currfix.count(x) == 0, act))
            if len(tmp) > 0:
                act = tmp
        # act = sorted(act, key=lambda x: prio.index(x))
        act = sorted(act, key=lambda x: self.children[x].subtree_size, reverse=True)
        # act = act[:4 if len(act) < 16 else int(ceil(len(act) / 4.))]
        # c = act[randint(0, len(act) - 1)]
        idx = (len(act) - 1) - floor(log2(randint(1, (2 ** len(act)) - 1)))
        c = act[idx]
        return c + self.children[c].select_with_tree_priority()

    def strike_leaf_on_path(self, word: str) -> bool:
        if self.is_leaf:
            return True
        if self.children[word[0]].strike_leaf_on_path(word[1:]):
            del self.children[word[0]]
        self.subtree_size -= 1
        return self.subtree_size == 0


class WordTree:
    freq_dict: Optional[dict] = None
    BLACK = 0
    YELLOW = 1
    GREEN = 2

    def __init__(self, word_len: int, wordlist: list[str]):
        if WordTree.freq_dict is None:
            WordTree.freq_dict = {}
            total_text = ''.join(wordlist)
            WordTree.freq_dict = {c: total_text.count(c) for c in ascii_lowercase}
        seed(time_ns())
        self.word_len: int = word_len
        for c in ascii_lowercase:  # Central control of letter appearance/positions
            LetterControl.make_letter_ctrl(c, word_len)
        self.word_tree_root: TreeNode = TreeNode(position=-1)  # Dummy
        self.word_tree_root.add_children(suffix_list=wordlist, word_len=self.word_len)

    @staticmethod
    def get_tree_priority():
        return sorted(list(WordTree.freq_dict), key=lambda k: WordTree.freq_dict[k], reverse=True)

    def get_next_word(self):
        return self.word_tree_root.select_with_tree_priority()

    def strike_word(self, word: str) -> None:
        self.word_tree_root.strike_leaf_on_path(word)

    def process_response(self, response: list[tuple]) -> None:
        for idx, res in enumerate(response):
            if res[1] == WordTree.BLACK:
                for i in range(self.word_len):
                    LetterControl.get_letter_ctrl(res[0]).mark_illegal_position(i)
            elif res[1] == WordTree.YELLOW:
                LetterControl.get_letter_ctrl(res[0]).mark_illegal_position(idx, other_implied=True)
            else:
                assert res[1] == WordTree.GREEN
                LetterControl.get_letter_ctrl(res[0]).mark_legal_position(idx)
                for c in ascii_lowercase:
                    if c != res[0]:
                        LetterControl.get_letter_ctrl(c).mark_illegal_position(idx)
        WordTree.freq_dict = {c: 0 for c in ascii_lowercase}
        self.word_tree_root.purge_inactive()
        return None
