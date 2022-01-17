#!/usr/bin/env python

import os

WORD_FILE_PATH = 'words_alpha.txt'

def main():
    words = load_words()
    print('Loaded {} words.'.format(len(words)))

def load_words():
    with open(get_word_file_path()) as word_file:
        return set(word_file.read().split())

def get_word_file_path():
    script_dir = os.path.dirname(__file__) 
    return os.path.join(script_dir, WORD_FILE_PATH)

if __name__ == '__main__':
    main()