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

import pandas as pd
import numpy as np

RTDIR = os.path.dirname(__file__)


class WordBank:
    """ The WordBank object represents all possible Wordle options
        as they narrow down with more guesses.
    """
    def __init__(self):
        self.word_bank = self.read_file()

        # When a letter is confirmed to a location (GREEN), it will be placed here
        self.confirmed = ["", "", "", "", ""]
        # When a letter is rejected (GREY OR YELLOW AT LOCATION), it will be placed here
        self.rejected = ["", "", "", "", ""]
        # If a letter is identified, but location is unknown (YELLOW), it will be placed here
        self.possible = ""

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

    def check(self, word: str, res: str):
        """ 

        Args:
            word (str): _description_
            res (str): _description_
        """
        for i, letter in enumerate(word):
            if res[i] == "2":
                self.confirmed[i] = letter
                # TODO: Should I remove letter from self.possible here?
            elif res[i] == "1":
                self.rejected[i] += letter
                self.possible += letter
            elif res[i] == "0":
                self.rejected[0] += letter
                self.rejected[1] += letter
                self.rejected[2] += letter
                self.rejected[3] += letter
                self.rejected[4] += letter
                self.possible.replace(letter, "")
        print(f"{self.confirmed=} | {self.rejected=} | {self.possible=}")

        # Generate a mask of the WordBank Dataframe by comparing the options with the known data
        mask = self.word_bank["Words"].apply(self.search)
        # Apply the mask on the Dataframe and drop all False entries
        self.word_bank = self.word_bank[mask].reset_index(drop=True)

        options = "\nNew Options Generated: "
        for choice in self.word_bank["Words"]:
            options += choice + ", "
        print(options[:-1])
        print()

        self.generate_probs()
        # self.word_bank["Odds"] = self.word_bank["Words"].apply(args=self.generate_probs)

        if self.word_bank["Words"].size == 1:
            return True
        if self.word_bank["Words"].size == 0:
            print("Error! No more options!")
            return True

    def generate_probs(self):
        alphabet = {
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

        # condition = self.word_bank["Words"].value_counts(subset=list(alphabet), )
        # print(condition)
        total = self.word_bank["Words"].size * 5
        print(f"Choosing from {self.word_bank['Words'].size} options...")
        bank = [alphabet.copy(),alphabet.copy(),alphabet.copy(),alphabet.copy(),alphabet.copy()]
        count = [0, 0, 0, 0, 0]
        # odds = np.array()

        for word in self.word_bank["Words"]:
            for i in range(5):
                if self.confirmed[i] == "":
                    letter = word[i]

                    alphabet[letter] += 1

                    bank[i][letter] += 1
                    count[i] += 1

        print(f"{total=}")
        print(alphabet)

        for i in range(5):
            print(bank[i])

        for i in range(5):
            if self.confirmed[i] == "":
                print(f"Slot {i+1} predicted: ")
                for key, val in bank[i].items():
                    if val != 0:
                        if count[i] > 0:
                            if val == count[i]:
                                print(f"Confirmed slot {i}: {key}")
                                self.confirmed[i] = key
                            print(f"\t{key} = {val*100/count[i]}")
            else:
                print(f"Slot {i+1} confirmed: {self.confirmed[i]}")

        print("Total Options:")
        for key, val in alphabet.items():
            if val > 0 and key not in self.possible:
                print(f"\t{key} = {val*100/total}%")

    def search(self, word: str):
        """ Helper function to be applied on the wordbank dataframe

        TODO: Optimizations could be made here to make the search more accurate

        Args:
            word (str): input string that is being compared

        Returns:
            bool: True if the word is a possible combination of letters
        """
        for i in range(5):
            # First, check to see if the letter is already confirmed
            if self.confirmed[i] != "":
                if word[i] != self.confirmed[i]:
                    return False
            # Second, check to see if any letters were rejected
            if word[i] in self.rejected[i]:
                return False
        # Finally, check to see that the word contains at least one of each possible letter
        # TODO: Later I will add more functionality to check for duplicate letters
        for c in self.possible:
            if not c in word:
                return False
        return True


if __name__ == "__main__":
    # Generate the Wordbank object (This loads the dictionary list)
    b = WordBank()

    # Enter each guess along with the results recieved from Wordle
    # GUESS = input("Enter first guess: ")
    GUESS = "crane"
    while len(GUESS) != 5 and not GUESS.isalpha():
        GUESS = input("Invalid entry! Can only be 5 characters and alphabetic! Try again: ")

    start = datetime.datetime.now()
    GUESS_COUNT = 1
    while GUESS != "q":
        # Prompt the user for what the results were
        # TODO: Potentially grab this automatically, either through webscraping or image processing
        RESULTS = ""
        while len(RESULTS) != 5 and not RESULTS.isnumeric():
            if RESULTS == "q":
                break
            RESULTS = input("What were the results? (2=green, 1=yellow, 0=grey) (ex. '02001'): ")

        # Check if the user won
        if RESULTS == "22222":
            print(f"\nCongrats! You solved the Wordle in {GUESS_COUNT} attempts! Final Answer = {GUESS}")
            break

        # Check if the user exceeded the guess limit
        if GUESS_COUNT >= 6:
            print("\nSorry, you've used all of your guesses")
            break

        # Perform the actual check and suggest next words
        # TODO: Display statistics here
        if b.check(GUESS.lower(), RESULTS):
            print(f"\nCongrats! You solved the Wordle in {GUESS_COUNT} attempts! Final Answer = {GUESS}")
            break

        # Prompt the user for their next guess
        # TODO: Eventually pick this automatically based on statistics
        GUESS = ""
        while len(GUESS) != 5 and not GUESS.isalpha():
            if GUESS == "q":
                break
            GUESS = input(f"Enter guess #{GUESS_COUNT+1} (or 'q' to quit): ")
        GUESS_COUNT += 1

    stop = datetime.datetime.now()
    print(f"This took {stop-start} seconds")
