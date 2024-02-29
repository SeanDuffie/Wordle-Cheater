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
        """_summary_

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

    def search(self, word):
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
    GUESS = input("Enter first guess: ")
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
        b.check(GUESS.lower(), RESULTS)

        # Prompt the user for their next guess
        # TODO: Eventually pick this automatically based on statistics
        GUESS = ""
        while len(GUESS) != 5 and not GUESS.isalpha():
            if GUESS == "q":
                break
            GUESS = input(f"Enter guess #{GUESS_COUNT} (or 'q' to quit): ")
        GUESS_COUNT += 1

    stop = datetime.datetime.now()
    print(f"This took {stop-start} seconds")
