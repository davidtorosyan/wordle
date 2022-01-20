#!/usr/bin/env python

import os

WORD_FILE_PATH = 'words_alpha.txt'
WORD_LENGTH = 5

RESPONSE_WRONG = 'b' # black
RESPONSE_CLOSE = 'y' # yellow
RESPONSE_RIGHT = 'g' # green

class State:
    def __init__(self):
        self.wrong = set()
        self.close = {}
        self.right = {}

    def fill(self, other):
        self.wrong.update(other.wrong)
        for (letter, indices) in other.close.items():
            for index in indices:
                self.mark_close(letter, index)
        self.right.update(other.right)

    def mark_wrong(self, letter):
        self.wrong.add(letter)

    def mark_close(self, letter, index):
        indices = self.close.get(letter, set())
        indices.add(index)
        self.close[letter] = indices

    def mark_right(self, letter, index):
        self.right[letter] = index

    def is_consistent(self):
        if self.wrong.intersection(self.close.keys()):
            return False
        if self.wrong.intersection(self.right.keys()):
            return False
        close_indices = set((letter, index) for (letter, indices) in self.close.items() for index in indices)
        if close_indices.intersection(self.right.items()):
            return False
        return True

    def __str__(self):
        return "Right: {}, Close: {}, Wrong: {}".format(
            self.right.__str__(),
            self.close.__str__(),
            self.wrong.__str__())

    def __repr__(self):
        return self.__str__()

def main():
    words = load_words()
    print('Loaded {} words.'.format(len(words)))
    play(words)

def play(words):
    knowledge = State()
    while True:
        print('Current knowledge: {}'.format(knowledge))
        guess = get_next_word(words, knowledge).upper()
        print('Guess: {}'.format(guess))
        response = input('Was it right? ')
        if (is_win(response)):
            print('Hooray!')
            break
        elif (is_loss(response)):
            print('Darn.')
            break
        else:
            info = parse(guess, response)
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
    state = State()
    state.fill(current_info)
    state.fill(new_info)
    return state

def is_win(response):
    return response == 'won'

def is_loss(response):
    return response == 'lost'

def parse(guess, response):
    if response is None or len(response) != WORD_LENGTH:
        return None
    result = State()
    for idx, char in enumerate(response):
        guess_char = guess[idx]
        if char == RESPONSE_WRONG:
            result.mark_wrong(guess_char)
        elif char == RESPONSE_CLOSE:
            result.mark_close(guess_char, idx)
        elif char == RESPONSE_RIGHT:
            result.mark_right(guess_char, idx)
        else:
            return None
    return result

def get_next_word(words, knowledge):
    filtered = filter_words(words, knowledge)
    ranked = rank_words(filtered, knowledge)
    return choose_word(ranked)

def filter_words(words, knowledge):
    return set([word for word in words if len(word) == WORD_LENGTH])

def rank_words(words, knowledge):
    return {word: 1.0 for word in words}

def choose_word(word_rankings):
    # sort by score, and then by word to break ties
    ranked = dict(sorted(word_rankings.items(), key=lambda item: (item[1], item[0])))
    return next(iter(ranked))

def load_words():
    with open(get_word_file_path()) as word_file:
        return set(word_file.read().split())

def get_word_file_path():
    script_dir = os.path.dirname(__file__) 
    return os.path.join(script_dir, WORD_FILE_PATH)

if __name__ == '__main__':
    main()