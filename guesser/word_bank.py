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
    def __init__(self, debug = False):
        self.debug = debug
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

    def submit_guess(self, word: str, res: str) -> str:
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

        # Parse results and update letter information
        for i, letter in enumerate(word):
            # If the correct letter is in the correct spot
            if res[i] == "2":
                self.confirmed[i] = letter
            # If the letter is present but in a different spot
            elif res[i] == "1":
                self.rejected[i] += letter
                self.possible += letter
            # If the letter is not present (or already confirmed)
            elif res[i] == "0":
                self.rejected[0] += letter
                self.rejected[1] += letter
                self.rejected[2] += letter
                self.rejected[3] += letter
                self.rejected[4] += letter
                self.possible.replace(letter, "")

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

        # Sort database based on probability of remaining options
        alphabet = self.generate_probs()
        self.word_bank["Odds"] = self.word_bank["Words"].apply(func=self.solution_odds, args=(alphabet,))
        self.word_bank.sort_values(by=["Odds"], ascending=False, inplace=True, ignore_index=True)
        if self.debug:
            print(self.word_bank)

        # Print out the next options for the user to pick
        if self.debug:
            options = "\nNew Options Generated: "
            for choice in self.word_bank["Words"]:
                options += choice + ", "
            print(options[:-2])
            print()

        return self.word_bank["Words"][0]

    def generate_probs(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        # Dictionary of all letters in the alphabet, and the percentage of occurances
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

        # Initialize all the containers and sizes
        total = self.word_bank["Words"].size * 5
        # if self.debug:
        #     print(f"Choosing from {self.word_bank['Words'].size} options...")
        bank = [alphabet.copy(),alphabet.copy(),alphabet.copy(),alphabet.copy(),alphabet.copy()]
        count = [0, 0, 0, 0, 0]

        for word in self.word_bank["Words"]:
            for i in range(5):
                # if self.confirmed[i] == "":
                letter = word[i]

                alphabet[letter] += 1
                bank[i][letter] += 1
                count[i] += 1

        # print(f"Total letters: {total}")
        # print(f"Total Odds: {alphabet}")


        # for i in range(5):
        #     print(f"Slot {i}: {bank[i]}")

        # Iterate over
        for i in range(5):
            if self.confirmed[i] == "":
                # print(f"Slot {i+1} predicted: ")
                for key, val in bank[i].items():
                    if val != 0:
                        if count[i] > 0:
                            # If all remaining options have the same letter, confirm it
                            if val == count[i]:
                                self.confirmed[i] = key

        # print("Total Options:")
        # for key, val in alphabet.items():
        #     if val > 0 and key not in self.possible:
        #         print(f"\t{key} = {val*100/total}%")

        return alphabet

    def solution_odds(self, word: str, alphabet: dict) -> float:
        """ Calculate the probability weight of each word in the remaining word bank options

        FIXME: This double counts the probability of repeating letters, while not always a problem, this likely reduces average accuracy
            - Factor in a separate count that just checks if the word contains a letter rather than total count
            - Factor in a separate count that checks per slot instead

        Args:
            word (str): The current word that is being analyzed
            alphabet (dict): a dictionary of all letters and percentage of occurences they have in the remaining word bank

        Returns:
            float: probability that the current word is the solution
        """
        odds = 1

        # 
        count = sum(alphabet.values())
        # if self.debug:
        #     print(f"Analyzing word: {word}")
        for i in range(5):
            # If the letter is already confirmed, it shouldn't affect the odds
            if self.confirmed[i] == "":
                # if self.debug:
                #     print(f"\t{word[i]} has a chance of {alphabet[word[i]]*100/count}")
                odds *= alphabet[ word[i] ] / count

        return odds * 100

    def search(self, word: str):
        """ Helper function to be applied on the wordbank dataframe

        TODO: Optimizations could be made here to make the search more accurate
        TODO: Handle duplicate letters
        TODO: Calculate probably based on letters in specific locations
        TODO: Calculate probability 

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
    GUESS_COUNT = 1

    # Enter each guess along with the results recieved from Wordle
    # GUESS = input("Enter first guess: ")
    GUESS = "crane"
    # GUESS = input("Invalid entry! Can only be 5 characters and alphabetic! Try again: ")

    start = datetime.datetime.now()
    while GUESS != "q":
        # Prompt the user for what the results were
        # TODO: Potentially grab this automatically, either through webscraping or image processing
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
        guess_response = b.submit_guess(GUESS.lower(), RESULTS)

        if guess_response == "Failed":
            print("Something went wrong!")
            break
        else:
            print(f"Suggested Next Guess: {guess_response}")
            GUESS = guess_response

        # Prompt the user for their next guess
        # GUESS = input(f"Enter guess #{GUESS_COUNT+1} (or 'q' to quit): ")
        # GUESS_COUNT += 1

    stop = datetime.datetime.now()
    print(f"This took {stop-start} seconds")
