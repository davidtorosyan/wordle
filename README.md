# wordle bot

## Table of contents

- [Introduction](#introduction)
- [Setup](#setup)
- [Usage](#usage)
- [Contribute](#contribute)

## Introduction

This is a solver for [wordle](https://www.powerlanguage.co.uk/wordle/).

The goal is to make a bot that can beat most humans (on average).

## Setup

Install python3.

No dependencies yet, so no setup environment.

## Usage

To use the tool, run:
```sh
python ./src/wordle.py
```

Here's some example output:
```
> python ./src/wordle.py
Loaded 12972 words.
Round 1, guess: SEASE
Was it right? bbybb
Round 2, guess: RORAL
Was it right? bbbyb
Round 3, guess: NANNA
Was it right? bggbb
Round 4, guess: TANTY
Was it right? bggbb
Round 5, guess: MANIC
Was it right? bgggg
Round 6, guess: PANIC
Was it right? ggggg
Hooray!
```

You can also run in test mode to see how it performs for a specific word:
```
> python ./src/wordle.py -t panic
Loaded 12972 words.
Running test for word: PANIC
Round 1, guess: SEASE
Was it right? ⬛⬛🟨⬛⬛
Round 2, guess: RORAL
Was it right? ⬛⬛⬛🟨⬛
Round 3, guess: NANNA
Was it right? ⬛🟩🟩⬛⬛
Round 4, guess: TANTY
Was it right? ⬛🟩🟩⬛⬛
Round 5, guess: MANIC
Was it right? ⬛🟩🟩🟩🟩
Round 6, guess: PANIC
Was it right? 🟩🟩🟩🟩🟩
Hooray!

Wordle bot 6/6

⬛⬛🟨⬛⬛
⬛⬛⬛🟨⬛
⬛🟩🟩⬛⬛
⬛🟩🟩⬛⬛
⬛🟩🟩🟩🟩
🟩🟩🟩🟩🟩
```

You can also run it for a set of test words and get statistics:
```
> python ./src/wordle.py -s boost tiger query drink     
Loaded 12972 words.
BOOST: 3
TIGER: 4
QUERY: 5
DRINK: 5

STATISTICS
Played: 4, Win %: 100%, Won: 4, Failed: 0, Mean: 4.2
1: 0
2: 0
3: 1 🟩
4: 1 🟩
5: 2 🟩🟩
6: 0
```

To see all options, run:
```sh
python src/wordle.py -h
```

## Contribute

This repo isn't quite ready for contributions yet, but message me if you're interested.

A couple of notes:
* `word_lists/alpha.txt` sourced from [dwyl/english-words](https://github.com/dwyl/english-words).
* `word_lists/wordle.txt` sourced from the JavaScript of the wordle site.