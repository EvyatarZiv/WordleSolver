from english_words import get_english_words_set
from random import seed, randint
from time import time_ns
from WordTree import WordTree
import argparse
import logging

logger = logging.getLogger('main')

WORD_LEN = 5
WORD_LIST = []

OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[00m'


def fmt_resp(res: tuple) -> str:
    if res[1] == WordTree.GREEN:
        fmt_clr = OKGREEN
    else:
        fmt_clr = '' if res[1] == WordTree.BLACK else WARNING
    return f'{fmt_clr}{res[0]}{ENDC}'


def init_wordlist():
    global WORD_LIST
    allwords = get_english_words_set(['web2'], alpha=True,
                                     lower=True)  # get_english_words_set(['gcide', 'web2'], alpha=True, lower=True)
    WORD_LIST = list(filter(lambda x: len(x) == WORD_LEN and x.isalpha(), allwords))


def select_random_words(n_words: int = 100) -> list[str]:
    seed(time_ns())
    words = []
    for i in range(n_words):
        words.append(WORD_LIST[randint(0, len(WORD_LIST) - 1)])
    return words


def compare_to_ans(guess: str, word: str) -> list[tuple]:
    assert len(guess) == len(word)
    resp = []
    for idx, c in enumerate(guess):
        if word.count(c) == 0:
            resp.append((c, WordTree.BLACK))
        elif word[idx] != c:
            text = ''.join([word[i] for i in range(len(word)) if word[i] != guess[i]])
            if text.count(c) > 0:
                resp.append((c, WordTree.YELLOW))
            else:
                resp.append((c, WordTree.BLACK))
        else:
            resp.append((c, WordTree.GREEN))
    return resp


_DEBUG_RCTR = 0


def guess_word(word: str, n_guesses: int = 6) -> tuple[bool, int]:
    global _DEBUG_RCTR
    _DEBUG_RCTR += 1
    logger.debug(f'Entering round #{_DEBUG_RCTR}')
    wt: WordTree = WordTree(WORD_LEN, WORD_LIST)
    for i in range(n_guesses):
        guess = wt.get_next_word()
        resp: list[tuple] = compare_to_ans(guess=guess, word=word)
        logger.debug(f'Guess #{i + 1}: {"".join([fmt_resp(res) for res in resp])}')
        if guess == word:
            logger.debug(f'{OKGREEN}CORRECT!{ENDC}')
            return True, i + 1
        wt.process_response(resp)
    logger.debug(f'{FAIL}FAILED!{ENDC}\nThe word was {word}')
    return False, n_guesses


def parse_response(guess: str):
    while True:
        raw = input("Input guess result:")
        if len(raw) != 3 * WORD_LEN - 1 or (not (set(list(raw[::3])) <= {'b', 'y', 'g'})) or raw[1::3] != guess or set(
                list(raw[2::3])) != {','}:
            logger.info(f'Input should be formatted as follows: <[b,y,g]><letter>,...,<[b,g,y]><letter>')
            continue

        def get_rep(x):
            return WordTree.BLACK if x == 'b' else (WordTree.GREEN if x == 'g' else WordTree.YELLOW)

        return [(raw[i:i + 3][1], get_rep(raw[i:i + 3][0])) for i in range(0, len(raw), 3)]


def interactive_main(ng: int) -> None:
    wt: WordTree = WordTree(WORD_LEN, WORD_LIST)
    for i in range(ng):
        while True:
            guess = wt.get_next_word()
            logger.info(f'Guess #{i + 1}: {guess}')
            if input("Word recognized? ") != "n":
                break
            wt.strike_word(guess)
        resp = parse_response(guess)
        logger.info(f'Guess #{i + 1} result: {"".join([fmt_resp(res) for res in resp])}')
        wt.process_response(resp)
        if set([res[1] for res in resp]) == {WordTree.GREEN}:
            break
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='WordleSolver')
    parser.add_argument('-ng', type=int, choices=range(1, 100), required=False, default=6, action='store',
                        dest='ng')
    parser.add_argument('--interactive', type=bool, required=False, default=False, action='store', dest='inter')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s')
    init_wordlist()
    if args.inter:
        interactive_main(args.ng)
        return None
    words = select_random_words(n_words=1000)
    count = 0
    sum_guesses = 0
    ng_hist = {n: 0 for n in range(1, args.ng + 1)}
    for word in words:
        res = guess_word(word, n_guesses=args.ng)
        count += res[0]
        sum_guesses += res[1]
        ng_hist[res[1]] += 1
    logger.info(
        f'Correctly guessed {100. * (count / len(words))} percent of the words\n'
        f'Average number of guesses per round was {sum_guesses / len(words)}\n'
        f'Guess number histogram:\n'
        f'{ng_hist}')


if __name__ == '__main__':
    main()
