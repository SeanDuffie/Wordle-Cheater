""" @file word_bank.py
    @author Sean Duffie
    @brief This program is intended to automatically solve the NYT Wordle puzzle.

    More features will be added to this in the future, but for now it just reads guesses
    and filters from a wordbank of options

    TODO: calculate statistics on which letters are most valuable to identify
    TODO: Guessing logic for automatic picking
"""
import datetime
import os
from typing import Literal

import pandas as pd

RTDIR = os.path.dirname(__file__)

import difflib


def exact_comp(first_word, second_word):
    """_summary_

    Resources:
        Stack Overflow: https://stackoverflow.com/questions/682367/good-python-modules-for-fuzzy-string-comparison
        Hamming Distance: https://en.wikipedia.org/wiki/Hamming_distance
            (Distance of two strings from each other)
        Smith-Waterman Algorithm: https://en.wikipedia.org/wiki/Smith–Waterman_algorithm
            (Used for DNA sequences)
        Levenshtein Distance: https://en.wikipedia.org/wiki/Levenshtein_distance
            ("Edit Distance": commonly used for spell checking)
        difflib.SequenceMatcher:
            calculate ratio similar to Levenshtein Distance
            built-in, but 
        JellyFish: https://pypi.python.org/pypi/jellyfish/
            overkill, but still cool because it includes phonetic matching with other comparisons
        TheFuzz: https://stackoverflow.com/questions/17388213/find-the-similarity-metric-between-two-strings
            https://github.com/seatgeek/thefuzz

    Args:
        word_list (_type_): _description_
    """
    # score = difflib.SequenceMatcher(None, " ower", word).ratio()
    score = difflib.SequenceMatcher(None, first_word, second_word).ratio()
    return score

class WordBank:
    """ The WordBank object represents all possible Wordle options
        as they narrow down with more guesses.
    """
    def __init__(self, debug = False):
        self.debug = debug
        self.original_bank = self.read_file()
        self.word_bank = self.original_bank.copy()
        self.guess_count = 0

        # When a letter is confirmed to a location (GREEN), it will be placed here
        self.confirmed = ["", "", "", "", ""]
        self.confirmed_count = 0
        # When a letter is rejected (GREY OR YELLOW AT LOCATION), it will be placed here
        self.rejected = ["", "", "", "", ""]
        # If a letter is identified, but location is unknown (YELLOW), it will be placed here
        self.possible = ""

        # problem_words = []
        # for it, row1 in self.original_bank.iterrows():
        #     word1 = row1["Words"]
        #     for row2 in self.original_bank.iterrows():
        #         word2 = row2["Words"]

        # tot_alpha, con_alpha, slot_alpha = self.generate_probs()
        # self.original_bank["Slot Odds"] = self.original_bank["Words"].apply(func=self.solution_odds, args=(slot_alpha,True))
        # self.original_bank.sort_values(by=["Slot Odds"], ascending=False, inplace=True, ignore_index=True)
        # print(self.original_bank)

    def read_file(self):
        """ Reads in the word bank downloaded from the interned, then parses for only valid words

        Returns:
            pd.Dataframe: Single column Dataframe that has all possible 5 letter words
        """
        def valid_word(word: str):
            """ Helper function intended to be "apply()"'d on a pandas dataframe column

            Checks to make sure that a string contains only letters and is 5 long

            Args:
                word (str): input string

            Returns:
                bool: True if the word is 5 letters and contains no numbers or special characters
            """
            if len(str(word)) == 5:
                return word.isalpha()
            return False

        file = pd.read_csv(filepath_or_buffer=f'{RTDIR}\\..\\words.csv', names=["Words"])
        mask = file["Words"].apply(valid_word)
        return file[mask].reset_index(drop=True)

    def submit_guess(self, word: str, res: str, method: Literal['cum', 'uni', 'slo', 'tot']) -> str:
        """ Update the database off of recent guess, then select the next most likely
        (or most productive) option to make progress

        Args:
            word (str): Guess that will be used to modify the word bank
            res (str): Results from the guess, 2 is correct, 1 is present, 0 is rejected

        Returns:
            str: recommended next guess based on probability algorithm
        """
        # User Input error handling assertions
        assert len(word) == 5
        assert len(res) == 5
        assert word.isalpha()
        assert res.isnumeric()
        self.guess_count += 1

        # Parse results and update letter information
        for i, letter in enumerate(word):
            # If the correct letter is in the correct spot
            if res[i] == "2":
                self.confirmed[i] = letter
                # In case a duplicate letter occurs before this slot is confirmed, remove the letter from rejected
                self.rejected[i].replace(letter, "")
            # If the letter is present but in a different spot
            elif res[i] == "1":
                self.rejected[i] += letter
                self.possible += letter
            # If the letter is not present (or already confirmed)
            elif res[i] == "0":
                # TODO: Test and see what happens if the previous duplicate is confirmed
                # If letter is rejected, it checks for duplicate letters before rejecting all slots
                loc = word.index(letter)
                if loc != i and res[loc] in ["1", "2"]:
                    self.rejected[i] += letter
                # If there are no duplicate letters, remove from possibilities and reject all slots
                else:
                    self.possible.replace(letter, "")
                    for j in range(5):
                        if self.confirmed[j] != letter:
                            self.rejected[j] += letter

        count = 0
        for c in self.confirmed:
            if c != "":
                count += 1
        self.confirmed_count = count

        # DEBUG: Display all current categories of characters
        if self.debug:
            print(f"{self.confirmed=} | {self.rejected=} | {self.possible=}")

        # Generate a mask of the WordBank Dataframe by comparing the options with the known data
        mask = self.word_bank["Words"].apply(self.search)
        # Apply the mask on the Dataframe and drop all False entries
        self.word_bank = self.word_bank[mask].reset_index(drop=True)

        # Stop the guessing process if the database is empty (this should not happen)
        if self.word_bank["Words"].size == 0:
            print("Error! No more options!")
            return "Failed"

        # Calculate the probability of remaining options and append as a column (based on config)
        tot_alpha, con_alpha, slot_alpha = self.generate_probs()
        if method in ['cum', 'tot']:
            self.word_bank["Cumul Odds"] = self.word_bank["Words"].apply(
                func=self.solution_odds,
                args=(tot_alpha,)
            )
            # TEMP: test with whole bank
        if method in ['uni', 'tot']:
            self.word_bank["Unique Odds"] = self.word_bank["Words"].apply(func=self.solution_odds, args=(con_alpha,))
            # TEMP: test with whole bank
        if method in ['slo', 'tot']:
            self.word_bank["Slot Odds"] = self.word_bank["Words"].apply(func=self.solution_odds, args=(slot_alpha,True))
            # TEMP: test with whole bank
            self.original_bank["Slot Odds"] = self.original_bank["Words"].apply(func=self.solution_odds, args=(slot_alpha,True))

        # If combining configurations, generate a new column will all other data
        if method == 'tot':
            # Combine all of the odds
            def sum_cats(row):
                return row["Cumul Odds"] * row["Unique Odds"] * row["Slot Odds"]
            self.word_bank["Total Odds"] = self.word_bank.apply(func=sum_cats, axis=1)

        # Sort the Dataframe based on configuration
        words = ["", "", "", ""]
        if method == 'cum':
            self.word_bank.sort_values(by=["Cumul Odds"], ascending=False, inplace=True, ignore_index=True)
            words[0] = self.word_bank["Words"][0]
        elif method == 'uni':
            self.word_bank.sort_values(by=["Unique Odds"], ascending=False, inplace=True, ignore_index=True)
            words[1] = self.word_bank["Words"][0]
        elif method == 'slo':
            self.word_bank.sort_values(by=["Slot Odds"], ascending=False, inplace=True, ignore_index=True)
            words[2] = self.word_bank["Words"][0]
        elif method == 'tot':
            self.word_bank.sort_values(by=["Total Odds"], ascending=False, inplace=True, ignore_index=True)
            words[3] = self.word_bank["Words"][0]
        else:
            print("Invalid probability calculation configuration!")

        def find_bridge(word, char_list):
            score = 0
            for l in char_list:
                if l in word:
                    score += .2
            return score

        # TODO: The original bank should only be used to eliminate similar words
        oddballs = ""
        flag = False
        if word == "cower" and res == "02022":
            oddballs = "pmgbkvnx"
            flag = True
        elif word == "baste" and res == "02222":
            oddballs = "ptwc"
            flag = True
        elif word == "grace" and res == "22202":
            oddballs = "vtdpz"
            flag = True
        elif word == "share" and res == "22202":
            oddballs = "dkmpv"
            flag = True
        elif word == "watch" and res == "02222":
            oddballs = "bchpw"
            flag = True

        if flag:
            # Search the original bank for words that may eliminate the missing letters
            self.original_bank["Sim"] = self.original_bank["Words"].apply(func=find_bridge, args=(oddballs,))

            # Drop values that don't score high enough
            index_sim = self.original_bank[(self.original_bank['Sim'] <= 0.4)].index
            self.original_bank.drop(index_sim, inplace=True)

            # Sort the filtered results and reset the index
            self.original_bank.sort_values(by=["Sim"], ascending=False, inplace=True, ignore_index=True)
            self.original_bank = self.original_bank.reset_index(drop=True)

            # Return the most likely suggested word
            return self.original_bank["Words"][0]

        # Print results to user if they are actively participating
        if self.debug:
            print("\nRemaining:")
            print(self.word_bank)
            print(f"Cumul sug: {words[0]},\t Unique sug: {words[1]},\t Slot sug: {words[2]},\t Total sug: {words[3]}")

        return self.word_bank["Words"][0]

    def generate_probs(self):
        """ Generate the value of each individual letter in a word, this will later be used to
            calculate the value of a word towards narrowing down the remaining options.

        NOTE: This should only be done for remaining words. Word value can be calculated on a word
                that is known to be wrong, but would ruin the statistics for letter value.

        NOTE: Technically this isn't a probability, all remaining words should have equal
                probability, but some words will narrow down the remaining options for future
                guesses more than others on a failed guess, hence the term "value".

        Returns:
            tuple: contains 3 dictionaries that show (for each letter) the total count, the
                    count per slot (5), and the amount of words that contain each letter
        """
        # Dictionary of all letters in the alphabet, and the percentage of occurances
        total_alphabet = {
            "a": 0,
            "b": 0,
            "c": 0,
            "d": 0,
            "e": 0,
            "f": 0,
            "g": 0,
            "h": 0,
            "i": 0,
            "j": 0,
            "k": 0,
            "l": 0,
            "m": 0,
            "n": 0,
            "o": 0,
            "p": 0,
            "q": 0,
            "r": 0,
            "s": 0,
            "t": 0,
            "u": 0,
            "v": 0,
            "w": 0,
            "x": 0,
            "y": 0,
            "z": 0
        }
        # Copy of alphabet dictionary that will only count the first occurance of each letter
        contains_alphabet = total_alphabet.copy()
        # Contains an alphabet dictionary for each slot in the word
        slot_alphabet = [ total_alphabet.copy() for _ in range(5) ]

        for word in self.word_bank["Words"]:
            processed = ""
            for i in range(5):
                # if self.confirmed[i] == "":
                letter = word[i]

                # Count occurances of each letter in the remaining options. Good for presence. (1)
                total_alphabet[letter] += 1

                # Similar to above, but slot specific. This is better for correct placement. (2)
                slot_alphabet[i][letter] += 1

                # Only count the first occurance of each letter. Different statistic for duplicates
                if letter not in processed:
                    contains_alphabet[letter] += 1
                    processed += letter

        # # Iterate over letters an additional time
        # for i in range(5):
        #     # If letter is confirmed, skip it
        #     if self.confirmed[i] == "":
        #         # Iterate through statistics dictionary
        #         for key, val in slot_alphabet[i].items():
        #             # If all remaining options have the same letter, confirm it
        #             if val > 0 and val == sum(slot_alphabet[i].values()):
        #                 self.confirmed[i] = key

        return total_alphabet, contains_alphabet, slot_alphabet

    def solution_odds(self, word: str, alphabet: dict, slot: bool = False) -> float:
        """ Calculate the value of a word based on the count of letters in the remaining word bank
            options. This will be applied on the whole pandas dataframe wordbank

        NOTE: Technically this isn't a probability, all remaining words should have equal
                probability, but some words will narrow down the remaining options for future
                guesses more than others on a failed guess, hence the term "value".

        TODO: The efficiency of guesses could potentially be improved by guessing a word that is
                known to be false, but would narrow down the remaining options more. Although one
                guess is wasted, it could save you from wasting more if several remaining options
                are similar.

        TODO: I believe that you could also improve the odds calculation by selectively applying
                the slots calculation on words with duplicate letters. I'm curious to see the
                impact of slots when the statistics are applied on the original wordbank vs the
                narrowed wordbank.

        TODO: I've added the alternate probability options, but they can all be applied
                simulaneously to save time iterating

        Args:
            word (str): The current word that is being analyzed
            alphabet (dict): a dictionary of all letters and percentage of occurences they have in
                                the remaining word bank
            slot (bool): whether the input alphabet is per slot or cumulative

        Returns:
            float: the weighted value that the word has in narrowing down the options
        """
        odds = 100

        if slot:
            count = [0, 0, 0, 0, 0]
            for i in range(5):
                count[i] = sum(alphabet[i].values())
            # print(f"\t{word}: {count=} | {alphabet[0][word[0]]} | {alphabet[1][word[1]]} | {alphabet[2][word[2]]} | {alphabet[3][word[3]]} | {alphabet[4][word[4]]}")
        else:
            # Total letters that were counted
            count = sum(alphabet.values())
            # print(f"\t{word}: {count=} | {alphabet[word[0]]} | {alphabet[word[1]]} | {alphabet[word[2]]} | {alphabet[word[3]]} | {alphabet[word[4]]}")

        for i in range(5):
            letter = word[i]

            # If the letter is already confirmed, it shouldn't affect the odds
            if self.confirmed[i] == "":
                # If the statistics were gathered per slot, calculate accordingly
                if slot:
                    odds *= alphabet[i][letter] / count[i]
                    # print(f"\tSlot Count = {alphabet[i][letter]} / {count[i]}")
                else:
                    # TODO: Improve here
                    odds *= alphabet[letter] / count
                    # print(f"\tNorm Count = {alphabet[letter]} / {count}")
            # print(f"\tOdds after {letter}: {odds}")

        return odds

    def search(self, word: str):
        """ Helper function to be applied on the wordbank dataframe

        TODO: Optimizations could be made here to make the search more accurate
        TODO: Handle duplicate letters

        Args:
            word (str): input string that is being compared

        Returns:
            bool: True if the word is a possible combination of letters
        """
        for i in range(5):
            # First, check to see if the letter is already confirmed, if so, skip to next character
            if self.confirmed[i] != word[i]:
                # If it's confirmed, but mismatched, then reject the word
                if self.confirmed[i] != "":
                    return False
                # Second, check to see if any letters were rejected
                if word[i] in self.rejected[i]:
                    return False
        # Finally, check to see that the word contains at least one of each possible letter
        for c in self.possible:
            if not c in word:
                return False
        return True


if __name__ == "__main__":
    # Generate the Wordbank object (This loads the dictionary list)
    b = WordBank(debug=True)
    # b.submit_guess(word="     ", res="00000", method="tot")
    # GUESS_COUNT = 1

    # # Enter each guess along with the results recieved from Wordle
    # # GUESS = input("Enter first guess: ")
    # GUESS = "crane"
    # # GUESS = input("Invalid entry! Can only be 5 characters and alphabetic! Try again: ")

    # start = datetime.datetime.now()
    # while GUESS != "q":
    #     # Prompt the user for what the results were
    #     # TODO: Potentially grab this automatically, either through webscraping or image processing
    #     RESULTS = input("What were the results? (2=green, 1=yellow, 0=grey) (ex. '02001'): ")

    #     # Check if the user won
    #     if RESULTS == "22222":
    #         print(f"\nCongrats! You solved the Wordle in {GUESS_COUNT} attempts! Final Answer = {GUESS}")
    #         break

    #     # Check if the user exceeded the guess limit
    #     if GUESS_COUNT >= 6:
    #         print("\nSorry, you've used all of your guesses")
    #         break

    #     # Perform the actual check and suggest next words
    #     guess_response = b.submit_guess(word=GUESS.lower(), res=RESULTS, method='tot')

    #     if guess_response == "Failed":
    #         print("Something went wrong!")
    #         break
    #     else:
    #         print(f"Suggested Next Guess: {guess_response}")
    #         GUESS = guess_response

    #     # Prompt the user for their next guess
    #     # GUESS = input(f"Enter guess #{GUESS_COUNT+1} (or 'q' to quit): ")
    #     # GUESS_COUNT += 1

    # stop = datetime.datetime.now()
    # print(f"This took {stop-start} seconds")
