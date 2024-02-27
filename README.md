# Wordle-Cheater
This program should give me an advantage over my friends when it comes to the daily Wordle Challenge. It should either be able to play automatically, or be used as an assistive tool to a human user.

## Feature List

- [ ] Either an image reader to read the current guesses and determine their color
- [ ] Or a web scraper to pull directly from the HTML
- [ ] Ability to type in it's own guesses through pynput or some other keyboard library
- [ ] Time the duration that it takes to guess
- [x] Measure number of possible permutations for each guess
- [x] Eliminate spaces from the permutation when guessed correctly
- [x] Eliminate invalid letters from permutation when detected
- [x] Do a spell check before each guess - https://replit.com/talk/ask/How-to-check-if-a-word-is-an-English-word-with-Python/31374 
- [x] Allow preview of all possible valid words to the user
