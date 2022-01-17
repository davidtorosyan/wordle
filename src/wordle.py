#!/usr/bin/env python

import os

WORD_FILE_PATH = 'words_alpha.txt'
WORD_LENGTH = 5

def main():
    words = load_words()
    print('Loaded {} words.'.format(len(words)))
    guess = get_next_word(words)
    print('Guess {}'.format(guess.upper()))

def get_next_word(words):
    filtered = filter_words(words)
    ranked = rank_words(filtered)
    return choose_word(ranked)

def filter_words(words):
    return set([word for word in words if len(word) == WORD_LENGTH])

def rank_words(words):
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