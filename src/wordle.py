#!/usr/bin/env python

import argparse
import itertools
import os
import random
import string

from collections import defaultdict

ALPHA_FILE_PATH = 'word_lists/alpha.txt'
WORDLE_FILE_PATH = 'word_lists/wordle.txt'
DEFAULT_WORD_LENGTH = 5
DEFAULT_ROUNDS = 6
DEFAULT_TEST_SET = ['REBUS', 'BOOST', 'TRUSS', 'SIEGE', 'TIGER', 'BANAL', 'SLUMP', 'CRANK', 'GORGE', 'QUERY', 'DRINK', 'FAVOR', 'ABBEY', 'TANGY', 'PANIC', 'SOLAR', 'SHIRE', 'PROXY', 'POINT']
TOP_CHOICES_COUNT = 5
RANK_PRECISION = 4
RANK_HEURISTIC_MIN_COUNT = 100
RANK_HEURISTIC_NO_CHANGE_COUNT = 10
RANK_HEURISTIC_TRY_TO_WIN_COUNT = 10

STATS_BAR_MAX_LENGTH = 10
STATS_BAR_CHAR = '🟩'

RESPONSE_WRONG = 'b' # black
RESPONSE_CLOSE = 'y' # yellow
RESPONSE_RIGHT = 'g' # green

RESPONSE_WRONG_EMOJI = '⬛' # black
RESPONSE_CLOSE_EMOJI = '🟨' # yellow
RESPONSE_RIGHT_EMOJI = '🟩' # green

class State:
    def __init__(self, word_length):
        self.required = {}
        self.spots = []
        self.word_length = word_length
        for idx in range(0, self.word_length):
            self.spots.append(set(string.ascii_uppercase))

    def fill(self, other):
        for letter, num in other.required.items():
            self.required[letter] = max(self.required.get(letter, 0), num)
        for idx, spot in enumerate(self.spots):
            spot.intersection_update(other.spots[idx])

    def mark_wrong(self, letter, index):
        self.spots[index].discard(letter)

    def mark_close(self, letter, index):
        self.spots[index].discard(letter)
        self.required[letter] = self.required.get(letter, 0) + 1

    def mark_right(self, letter, index):
        self.spots[index].clear()
        self.spots[index].add(letter)
        self.required[letter] = self.required.get(letter, 0) + 1

    def mark_wrong_everywhere(self, letter):
        for spot in self.spots:
            # don't mess with the spot if it's already solved
            if len(spot) > 1:
                spot.discard(letter)

    def is_consistent(self):
        for spot in self.spots:
            if not spot:
                return False
        if sum(self.required.values()) > self.word_length:
            return False
        for letter, count in self.required.items():
            if count > self.count_spots_with_letter(letter):
                return False
        return True

    def count_spots_with_letter(self, letter):
        count = 0
        for spot in self.spots:
            if letter in spot:
                count += 1
        return count

    def __str__(self):
        options = [''.join(sorted(spot)) for spot in self.spots]
        return 'Required: {}, Options: {}'.format(
            self.required.__str__(),
            options.__str__())

    def __repr__(self):
        return self.__str__()

def main():
    args = get_parser().parse_args()
    word_file = ALPHA_FILE_PATH if args.word_length != 5 or args.expanded_word_list else WORDLE_FILE_PATH
    test_word = args.test_word.upper() if args.test_word else None
    test_set = DEFAULT_TEST_SET if args.test_set == [] else args.test_set
    words = load_words(word_file)
    print('Loaded {} words.'.format(len(words)))
    if args.test_all or test_set:
        test_many(words, args.word_length, args.rounds, test_set)
    else:
        play(words, args.word_length, args.rounds, test_word, False, args.debug)

def get_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="""Solver for wordle at https://www.powerlanguage.co.uk/wordle/

When prompted for the result of a guess, you can respond with letters instead of colors, like:
    {} = {}
    {} = {}
    {} = {}
    """.format(
        RESPONSE_RIGHT_EMOJI, RESPONSE_RIGHT,
        RESPONSE_CLOSE_EMOJI, RESPONSE_CLOSE,
        RESPONSE_WRONG_EMOJI, RESPONSE_WRONG))
    parser.add_argument('-l', '--word-length', type=int, default=DEFAULT_WORD_LENGTH, 
                        help='The word length ({} by default), non-default implies --expanded-word-list'.format(DEFAULT_WORD_LENGTH))
    parser.add_argument('-r', '--rounds', type=int, default=DEFAULT_ROUNDS, 
                        help='The number of rounds ({} by default)'.format(DEFAULT_ROUNDS))
    parser.add_argument('--expanded-word-list', dest='expanded_word_list', action='store_true',
                        help='If used, run against a larger dictionary.')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='Optional, if used print debug info')
    testing = parser.add_mutually_exclusive_group()
    testing.add_argument('-t', '--test-word', default=None, 
                        help='Optional, use to run a test against a word')
    testing.add_argument('-a', '--test-all', dest='test_all', action='store_true',
                        help='Optional, if used run a test against all words')
    testing.add_argument('-s', '--test-set', nargs='*', default=None,
                        help='Optional, if used run against a set of words (the words from January 2022 by default)')
    return parser

def test_many(words, word_length, max_rounds, test_set):
    eligible_words = test_set if test_set else sorted(word for word in words if len(word) == word_length)
    scores = [0] * max_rounds
    failed = 0
    for word in eligible_words:
        test_word = word.upper()
        score = play(words, word_length, max_rounds, test_word, True, False)
        if score is not None:
            scores[score-1] += 1
        else:
            failed += 1
        print('{}: {}'.format(test_word, score))
    success = sum(scores)
    played = success + failed
    win_percent = success / played
    mean_score = sum(((idx+1) * score for idx, score in enumerate(scores))) / success
    max_score = max(scores)
    scaled = max_score > STATS_BAR_MAX_LENGTH
    print('\nSTATISTICS\nPlayed: {}, Win %: {:.0%}, Won: {}, Failed: {}, Mean: {:.1f}'.format(played, win_percent, success, failed, mean_score))
    for idx, score in enumerate(scores):
        bar_length = int(score / max_score * STATS_BAR_MAX_LENGTH) if scaled else score
        bar = STATS_BAR_CHAR * bar_length
        print('{}: {} {}'.format(idx+1, score, bar))

def play(words, word_length, max_rounds, test_word, quiet, debug):
    if quiet and not test_word:
        raise Exception('Cannot run quiet without a test word!')
    if test_word:
        if not quiet:
            print('Running test for word: {}'.format(test_word))
    knowledge = State(word_length)
    round = 1
    responses = []
    remaining_words = filter_words(words, knowledge)
    while True:
        guess = get_next_word(words, remaining_words, knowledge, debug)
        if not guess:
            if not quiet:
                print('No eligible guess found, we lost!')
            return None
        if not quiet:
            print('Round {}, guess: {}'.format(round, guess))
        response = get_test_response(guess, test_word, quiet) if test_word else input('Was it right? ')
        if (is_not_word(response)):
            if not quiet:
                print('Okay, let\'s try again.')
            words.remove(guess)
            remaining_words.remove(guess)
        else:
            info = parse(guess, response, word_length)
            if not info:
                if not quiet:
                    print('Unable to parse response, try again!')
            elif not info.is_consistent():
                if not quiet:
                    print('Response is not self consistent, try again!')
            else:
                updated = merge(knowledge, info)
                if not updated.is_consistent():
                    if not quiet:
                        print('Response is not consistent with current state, try again!')
                elif is_win(response, word_length):
                    responses.append(response)
                    if not quiet:
                        print('Hooray!')
                        if test_word:
                            print('\nWordle bot {}/{}\n'.format(round, max_rounds))
                            for response in responses:
                                print(response)
                    return round
                elif (round >= max_rounds):
                    responses.append(response)
                    if not quiet:
                        print('Ran out of tries, we lost!')
                        if test_word:
                            print('\nWordle bot X/{}\n'.format(max_rounds))
                            for response in responses:
                                print(response)
                    return None
                else:
                    responses.append(response)
                    knowledge = updated
                    remaining_words = filter_words(remaining_words, knowledge)
                    round += 1

def get_test_response(guess, test_word, quiet):
    guess_list = list(guess)
    test_list = list(test_word)
    result = [''] * len(guess)
    for idx, char in enumerate(guess_list):
        if char == test_list[idx]:
            result[idx] = RESPONSE_RIGHT_EMOJI
            guess_list[idx] = ''
            test_list[idx] = ''
    for idx, char in enumerate(guess_list):
        if not char:
            continue
        test_idx = test_list.index(char) if char in test_list else None
        if test_idx is not None:
            result[idx] = RESPONSE_CLOSE_EMOJI
            guess_list[idx] = ''
            test_list[test_idx] = ''
    for idx, char in enumerate(guess_list):
        if not char:
            continue
        result[idx] = RESPONSE_WRONG_EMOJI
    response = ''.join(result)
    if not quiet:
        print('Was it right? {}'.format(response))
    return response

def merge(current_info, new_info):
    state = State(current_info.word_length)
    state.fill(current_info)
    state.fill(new_info)
    return state

def is_win(response, word_length):
    return response == RESPONSE_RIGHT * word_length or response == RESPONSE_RIGHT_EMOJI * word_length

def is_not_word(response):
    return response == 'what'

def parse(guess, response, word_length):
    if response is None or len(response) != word_length:
        return None
    result = State(word_length)
    wrong = set()
    close = set()
    for idx, char in enumerate(response):
        guess_char = guess[idx]
        if char == RESPONSE_WRONG or char == RESPONSE_WRONG_EMOJI:
            result.mark_wrong(guess_char, idx)
            wrong.add(guess_char)
        elif char == RESPONSE_CLOSE or char == RESPONSE_CLOSE_EMOJI:
            result.mark_close(guess_char, idx)
            close.add(guess_char)
        elif char == RESPONSE_RIGHT or char == RESPONSE_RIGHT_EMOJI:
            result.mark_right(guess_char, idx)
        else:
            return None
    wrong_everywhere = wrong - close
    for guess_char in wrong_everywhere:
        result.mark_wrong_everywhere(guess_char)
    return result

def get_next_word(words, remaining_words, state, debug):
    ranked = rank_words(words, remaining_words, state, debug)
    return choose_word(ranked, debug)

def filter_words(words, state):
    return [word for word in words if satisfied(word, state)]

def satisfied(word, state):
    if len(word) != state.word_length:
        return False
    for idx, char in enumerate(word):
        if char not in state.spots[idx]:
            return False
    for char, count in state.required.items():
        if word.count(char) < count:
            return False
    return True

def rank_words(words, remaining_words, state, debug):
    total = len(words)
    total_remaining = len(remaining_words)
    word_set = remaining_words if total_remaining < RANK_HEURISTIC_TRY_TO_WIN_COUNT else words
    if debug:
        print('Ranking {} words (with {} remaining) using knowledge: {}'.format(total, total_remaining, state))
    return {word: round(rank_word(word, remaining_words), RANK_PRECISION) for word in word_set}

def rank_word(word, words):
    max_partitions = pow(3, len(word))
    partitions = set()
    use_heuristic = len(words) > RANK_HEURISTIC_MIN_COUNT
    test_set = shuffle(words, word) if use_heuristic else words
    no_change_count = 0
    for target in test_set:
        response = get_test_response(word, target, True)
        no_change_count = no_change_count + 1 if response in partitions else 0
        partitions.add(response)
        if use_heuristic and no_change_count >= RANK_HEURISTIC_NO_CHANGE_COUNT:
            break
    rank = 1 - len(partitions) / max_partitions
    return rank

def shuffle(words, seed):
    random.seed(seed)
    size = len(words)
    override_spots = {}
    while size > 0:
        index = random.randint(0, size-1)
        if index in override_spots:
            choice = override_spots[index]
        else:
            choice = words[index]
        override_spots[index] = words[size-1]
        size -= 1
        yield choice

def choose_word(word_rankings, debug):
    # sort by score, and then by word to break ties
    if not word_rankings:
        return None
    ranked = dict(sorted(word_rankings.items(), key=lambda item: (item[1], item[0])))
    top = dict(itertools.islice(ranked.items(), TOP_CHOICES_COUNT))
    if debug:
        print('Ranked: {}'.format(top))
    return next(iter(top))

def load_words(path):
    with open(get_word_file_path(path)) as word_file:
        return list(sorted(word_file.read().upper().split()))

def get_word_file_path(path):
    script_dir = os.path.dirname(__file__) 
    return os.path.join(script_dir, path)

if __name__ == '__main__':
    main()