"""_summary_

Returns:
    _type_: _description_
"""

import datetime
import os

import pandas as pd
from word_bank import WordBank


RTDIR = os.path.dirname(__file__)


def check(guess, solution):
    result = ""

    for i in range(5):
        if guess[i] == solution[i]:
            result += "2"
        elif guess[i] in solution:
            result += "1"
        else:
            result += "0"

    return result

class Tester:
    def __init__(self) -> None:
        self.word_options = self.read_file()

        for start in self.word_options["Words"]:
            for solution in self.word_options["Words"]:
                wb = WordBank()
                guess_count = 1

                # print(f"TESTING FIRST GUESS: [{word1}] | WITH SOLUTION [{word2}]")
                result = check(start, solution)
                guess = wb.submit_guess(start, result)

                while result != "22222":
                    if guess == "Failed":
                        print("Error! Ran out of options! (This shouldn't be possible)")
                        break
                    guess_count += 1
                    # print(guess)
                    result = check(guess, solution)
                    guess = wb.submit_guess(guess, result)

                if guess_count > 6:
                    print(f"Solved [{solution}] in [{guess_count}] attempts, using [{start}] as a starting word!")

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


if __name__ == "__main__":
    t1 = Tester()
