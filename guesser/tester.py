"""_summary_

Returns:
    _type_: _description_
"""

import datetime
import os

import pandas as pd
from word_bank import WordBank
import random
import numpy as np


RTDIR = os.path.dirname(__file__)


def check(guess: str, solution: str) -> str:
    """ Generates a 'results' string from a guess when the solution is known

    Args:
        guess (str): the user or system generated guess
        solution (str): the known solution to the current puzzel iteration

    Returns:
        str: Formatted results string that compares the solution with the guess
    """
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
    """ Tester will be what gathers the statistical data from performance testing
    """
    def __init__(self) -> None:
        self.word_options = self.read_file()

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

    def play(self, start: str = "crane", solution: str = None, rand_sol: bool = False, manual: bool = False):
        """ Controls the actual play process of the game

        Args:
            start (str, optional): What should the first guess be? Defaults to "crane".
            solution (str, optional): What is the solution? (For simulation purposes) Defaults to Random.
            manual (bool, optional): Solve it manually or automatically? Defaults to False.
        """
        # Initialize wordbank and guess count, debug controls suppression of prints
        wb = WordBank(debug=manual)
        guess_count = 1
        guesses = [start]

        # If the solution is not defined, generate a random one
        if rand_sol:
            solution = wb.word_bank["Words"][random.randint(0,2309)]

        # If the solution is unknown, prompt user for results, otherwise generate them
        if solution is None:
            result = input("What were the results? (2=green, 1=yellow, 0=grey) (ex. '02001'): ")
        else:
            result = check(start, solution)

        # If playing manually, get next guess from user, otherwise generate next guess
        guess = wb.submit_guess(start, result)
        if manual:
            guess = input(f"Enter guess #{guess_count+1}: ")

        # Loop until the solution is found
        while result != "22222":
            # Check to make sure that the dataframe didn't run out of choices
            if guess == "Failed":
                print("Error! Ran out of options! (This shouldn't be possible)")
                break
            guess_count += 1

            # If the solution is unknown, prompt user for results, otherwise generate them
            if solution is None:
                result = input("What were the results? (2=green, 1=yellow, 0=grey) (ex. '02001'): ")
            else:
                guesses.append(guess)
                result = check(guess, solution)

            # Check if the user won
            if result == "22222":
                break

            # If playing manually, get next guess from user, otherwise generate next guess
            guess = wb.submit_guess(guess, result)
            if manual:
                guess = input(f"Enter guess #{guess_count+1}: ")

        # # Objective failed, continue solving for average statistics, but mark as failure
        # if guess_count > 6:
        #     print(f"Solved [{solution}] in [{guess_count}] attempts, using [{start}] as a starting word!")

        return guess_count, guesses

    def permutations(self):
        """ Runs through all the permutations of starting word compared to solution

            All other logic should be handled in the WordBank class
            TODO: Store results in a database
        """
        headers = ["First"]
        headers.extend(self.word_options["Words"])
        df = pd.DataFrame(columns=headers)

        other_headers = ["Start", "Average Score", "Min Score", "Max Score", "Failure Count", "Failures"]
        df2 = pd.DataFrame(columns=other_headers)

        # Loop through all starting words
        start_perm = datetime.datetime.now()
        for start in self.word_options["Words"]:
            headers.append(start)
            row = [start]
            failed = []

            start_word = datetime.datetime.now()
            # Loop through all potential solutions
            for solution in self.word_options["Words"]:
                count, guesses = self.play(start=start, solution=solution, manual=False)

                row.append(count)

                if count > 6:
                    failed.append((solution, count, guesses))

            stop_word = datetime.datetime.now()
            rrow = np.array(row[1:])
            print(f"Took {stop_word-start_word} seconds to process {start}")
            print(f"{start} scored an average of {rrow.mean()} and failed {len(failed)} times")

            row2 = [start, rrow.mean(), rrow.min(), rrow.max(), len(failed), failed]

            df.loc[len(df.index)] = row
            df2.loc[len(df2.index)] = row2

        stop_perm = datetime.datetime.now()
        print(f"Took {stop_perm-start_perm} seconds to complete the permutations")

        # df.sort_values(by=["Odds", ""], ascending=False, inplace=True, ignore_index=True)
        df2.sort_values(by=["Average Score", "Failure Count"], ascending=True, inplace=True, ignore_index=True)

        df.to_csv(path_or_buf="./permutations_full.csv", index=False)
        df2.to_csv(path_or_buf="./permutation_stats.csv", index=False)

        print(df)
        print(df2)


if __name__ == "__main__":
    t1 = Tester()

    t1.permutations()
    # print(t1.play(start="crane", solution="hunch", manual=True))
    # print(t1.play(start="crane", solution=None, manual=True))
