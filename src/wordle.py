#!/usr/bin/env python

import argparse
import os
import statistics
import string

ALPHA_FILE_PATH = 'word_lists/alpha.txt'
WORDLE_FILE_PATH = 'word_lists/wordle.txt'
DEFAULT_WORD_LENGTH = 5

RESPONSE_WRONG = 'b' # black
RESPONSE_CLOSE = 'y' # yellow
RESPONSE_RIGHT = 'g' # green

class State:
    def __init__(self, word_length):
        self.required = {}
        self.spots = []
        self.blocklist = set()
        self.word_length = word_length
        for idx in range(0, self.word_length):
            self.spots.append(set(string.ascii_uppercase))

    def fill(self, other):
        for letter, num in other.required.items():
            self.required[letter] = max(self.required.get(letter, 0), num)
        for idx, spot in enumerate(self.spots):
            spot.intersection_update(other.spots[idx])
        self.blocklist.update(other.blocklist)

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

    def not_word(self, word):
        self.blocklist.add(word)

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
    words = load_words(word_file)
    print('Loaded {} words.'.format(len(words)))
    play(words, args.word_length)

def get_parser():
    parser = argparse.ArgumentParser(description="Solver for wordle at https://www.powerlanguage.co.uk/wordle/")
    parser.add_argument("-l", "--word-length", type=int, default=DEFAULT_WORD_LENGTH, 
                        help="The word length ({} by default), non-default implies --expanded-word-list".format(DEFAULT_WORD_LENGTH))
    parser.add_argument("--expanded-word-list", dest="expanded_word_list", action="store_true",
                        help="If used, run against a larger dictionary.")
    return parser

def play(words, word_length):
    knowledge = State(word_length)
    while True:
        guess = get_next_word(words, knowledge)
        if not guess:
            print('No eligible guess found, we lost!')
            break
        print('Guess: {}'.format(guess))
        response = input('Was it right? ')
        if (is_win(response)):
            print('Hooray!')
            break
        elif (is_loss(response)):
            print('Darn.')
            break
        elif (is_not_word(response)):
            print('Okay, let\'s try again.')
            knowledge.not_word(guess)
        else:
            info = parse(guess, response, word_length)
            if not info:
                print('Unable to parse response, try again!')
            elif not info.is_consistent():
                print('Response is not self consistent, try again!')
            else:
                updated = merge(knowledge, info)
                if not updated.is_consistent():
                    print('Response is not consistent with current state, try again!')
                else:
                    knowledge = updated

def merge(current_info, new_info):
    state = State(current_info.word_length)
    state.fill(current_info)
    state.fill(new_info)
    return state

def is_win(response):
    return response == 'won'

def is_loss(response):
    return response == 'lost'

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
        if char == RESPONSE_WRONG:
            result.mark_wrong(guess_char, idx)
            wrong.add(guess_char)
        elif char == RESPONSE_CLOSE:
            result.mark_close(guess_char, idx)
            close.add(guess_char)
        elif char == RESPONSE_RIGHT:
            result.mark_right(guess_char, idx)
        else:
            return None
    wrong_everywhere = wrong - close
    for guess_char in wrong_everywhere:
        result.mark_wrong_everywhere(guess_char)
    return result

def get_next_word(words, state):
    filtered = filter_words(words, state)
    ranked = rank_words(filtered, state)
    return choose_word(ranked)

def filter_words(words, state):
    return set([word for word in words if satisfied(word, state)])

def satisfied(word, state):
    if len(word) != state.word_length:
        return False
    if word in state.blocklist:
        return False
    for idx, char in enumerate(word):
        if char not in state.spots[idx]:
            return False
    for char, count in state.required.items():
        if word.count(char) < count:
            return False
    return True

def rank_words(words, state):
    total = len(words)
    print('Ranking {} words using knowledge: {}'.format(total, state))
    composite = build_composite(words, state)
    return {word: rank_word(word, total, composite, state) for word in words}

def build_composite(words, state):
    result = []
    for idx in range(0, state.word_length):
        spot = {}
        for word in words:
            letter = word[idx]
            spot[letter] = spot.get(letter, 0) + 1
        result.append(spot)
    return result

def rank_word(word, total, composite, state):
    return statistics.mean((rank_letter(letter, total, composite[idx], state.spots[idx]) for idx, letter in enumerate(word)))

def rank_letter(letter, total, composite, spot):
    remaining_if_right = composite[letter]
    remaining_if_wrong = total - remaining_if_right
    probability_right = 1.0 / len(spot)
    probability_wrong = 1.0 - probability_right
    expected_remaining = probability_right * remaining_if_right + probability_wrong * remaining_if_wrong
    return expected_remaining / total

def choose_word(word_rankings):
    # sort by score, and then by word to break ties
    if not word_rankings:
        return None
    ranked = dict(sorted(word_rankings.items(), key=lambda item: (item[1], item[0])))
    return next(iter(ranked))

def load_words(path):
    with open(get_word_file_path(path)) as word_file:
        return set(word_file.read().upper().split())

def get_word_file_path(path):
    script_dir = os.path.dirname(__file__) 
    return os.path.join(script_dir, path)

if __name__ == '__main__':
    main()