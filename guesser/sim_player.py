""" @file sim_player.py
    @author Sean Duffie
    @brief Simulates a player with a known input. This can be done either for statistics or just simulating a playthrough.

TODO: Test if statistics are based on number of results left rather than letters eliminated
TODO: Test switching method mid round
TODO: If a method/starting word combo have a low amount of failures, maybe guessing one of the failures first can get you there faster?
TODO: https://stackoverflow.com/questions/53249133/check-if-a-pattern-is-in-a-list-of-words
"""

import datetime
import os
import random
from typing import Generator, Literal, Tuple

import numpy as np
import pandas as pd
from word_bank import WordBank

RTDIR = os.path.dirname(__file__)


class SimPlayer:
    """ SimPlayer will be what gathers the statistical data from performance testing
    """
    def __init__(self, solution: str = None, method: str = "slo") -> None:
        self.wb = WordBank()

        if solution is None:
            solution = self.wb.get_rand()

        assert solution in self.wb.original_bank["Words"]
        self.solution = solution

        assert method in ["cum", "uni", "slo", "tot"]
        self.method = method

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        pass

    def read_results(self, guess: str) -> str:
        """ Generates a 'results' string from a guess when the solution is known

        Args:
            guess (str): the user or system generated guess
            solution (str): the known solution to the current puzzel iteration

        Returns:
            str: Formatted results string that compares the solution with the guess
        """
        result = "00000"

        # First, eliminate all letters known to be correct, mask the correct letters with whitespace
        for i in range(5):
            if guess[i] == self.solution[i]:
                result = result[:i] + "2" + result[i+1:]
                guess = guess[:i] + " " + guess[i+1:]
                self.solution = self.solution[:i] + " " + self.solution[i+1:]
            # print(f"{guess=} | {self.solution=} | {result=}")

        # Next, identify all the characters that are present but not in the correct spot
        # Doing it this way allows you to identify duplicate letters without looping on confirmed
        # Additionally, only one "possible" duplicate letter should be marked for each duplicate
        for i in range(5):
            if guess[i] != " " and guess[i] in self.solution:
                result = result[:i] + "1" + result[i+1:]

                # Replace the character in self.solution with whitespace to handle duplicates
                j = self.solution.index(guess[i])
                self.solution = self.solution[:j] + " " + self.solution[j+1:]
            # print(f"{guess=} | {self.solution=} | {result=}")

        return result

    def run_generator(self, first: str = "flash", method: Literal['cum', 'uni', 'slo', 'tot'] = None) -> Generator[Tuple[str, str], None, None]:
        """ Main runner for RealPlayer """
        if method is not None:
            assert method in ["cum", "uni", "slo", "tot"]
            self.method = method

        assert len(first) == 5
        assert first.isalpha()
        assert first in self.wb.original_bank["Words"]
        guess = first

        while True:
            try:
                # Submit guess, then yield results
                result = self.read_results(guess=guess)

                # Check that the guess was accepted. TODO: If not, suggest a new one and continue.
                if result is None:
                    guess = "flash"
                    continue

                # Yield Generator output
                response = yield (guess, result)
                if response is not None:
                    assert len(response) == 5
                    assert first.isalpha()
                    assert first in self.wb.original_bank["Words"]
                guess = guess if response is None else response

                # Check victory conditions, or if out of guesses, get the final result
                if result == "22222" or result.isalpha():
                    return

                # Get suggestion from the wordbank for the next guess
                guess = self.wb.submit_guess(word=guess, res=result, method="slo")
            except AssertionError:
                if guess.lower() == "failed":
                    print("Error! Word Bank ran out of options! (This shouldn't be possible)")
                    return
                print(f"Invalid Guess: {guess}")

    # TODO: FIXME: Eventually change the typehinting for method to a more sophisticated dict or other typehint method
    def play(self, start: str = "crane", solution: str = None, method: Literal['cum', 'uni', 'slo', 'tot'] = 'tot',
             manual: bool = False):
        """ Controls the actual play process of the game

        Args:
            start (str, optional): What should the first guess be? Defaults to "crane".
            solution (str, optional): What is the solution? (For simulation purposes) Defaults to Random.
            manual (bool, optional): Solve it manually or automatically? Defaults to False.
        """
        # Initialize wordbank and guess count, debug controls suppression of prints
        wb = WordBank(debug=manual)
        guess_count = 1
        guesses = []
        guess = start

        # If the solution is not defined, generate a random one
        if solution == "rand":
            print(len(wb.word_bank["Words"]))
            solution = wb.word_bank["Words"][random.randint(0,2309)]

        while True:
            # If the solution is unknown, prompt user for results, otherwise generate them
            if solution is None:
                while True:
                    try:
                        result = input(f"What were the results for '{guess}'? (2=green, 1=yellow, 0=grey) (ex. '02001'): ")
                        if not len(result) == 5:
                            raise ValueError("Invalid Result size, must be 5 digits. Try Again.")
                        if not result.isnumeric():
                            raise ValueError("Result must be numerical (no special or letters). Try Again.")
                        if any(inv_num in result for inv_num in ['3', '4', '5', '6', '7', '8', '9']):
                            raise ValueError("Result can only contain [0, 1, 2]. Try Again.")
                        break
                    except ValueError as e:
                        print(e)
                        # logger.error(e)
            else:
                result = check(guess, solution)
                print(f"[{solution=}]: Guessing '{guess}' with results '{result}' on attempt {guess_count}")

            # Log result history
            guesses.append((guess, result))

            # Check for victory conditions
            if result == "22222":
                print("Victory!")
                break

            # If playing manually, get next guess from user, otherwise generate next guess
            guess = wb.submit_guess(guess, result, method)
            if manual:
                while True:
                    try:
                        guess = input(f"Enter guess #{guess_count+1}: ")
                        if not len(guess) == 5:
                            raise ValueError("Word must be 5 letters long. Try Again.")
                        if not guess.isalpha():
                            raise ValueError("Guess must be alphabetical (no special or numbers). Try Again.")
                        if not self.word_options["Words"].str.contains(guess).any():
                            print(self.word_options["Words"])
                            raise ValueError("Word guess must be in the Wordle database. Try Again.")
                        break
                    except ValueError as e:
                        print(e)
                        # logger.error(e)

            guess_count += 1

            # Check to make sure that the dataframe didn't run out of choices
            if guess.lower() == "failed":
                print("Error! Ran out of options! (This shouldn't be possible)")
                break

        # FIXME: Is guess_count necessary now that the guesses are logged as a list?
        return guess_count, guesses

def permutate(method: Literal['cum', 'uni', 'slo', 'tot'] = 'tot'):
    """ Runs through all the permutations of starting word compared to solution

        All other logic should be handled in the WordBank class
        TODO: Add multiprocessing here for faster runtimes
    """
    wb = WordBank()

    other_headers = ["Time", "Start", "Average Score", "Min Score", "Max Score", "Failure Count", "Failures"]
    df2 = pd.DataFrame(columns=other_headers)

    # Loop through all starting words
    time_start_perm = datetime.datetime.now()
    for start_word in ['flash']: # self.word_options["Words"]: # ['flash', 'caste', 'crane', 'worst']: #
        headers = ["Word", "Count"]
        df = pd.DataFrame(columns=headers)
        # TODO: Add multiprocessing here
        row = [start_word]
        failed = []

        time_start_word = datetime.datetime.now()
        # Loop through all potential solutions
        for solution in wb.original_bank():
            count, guesses = simulate(start=start_word, solution=solution, manual=False, method=method)

            row.append(count)
            df.loc[len(df.index)] = [solution, count]

            if count > 6:
                failed.append((solution, count, guesses))

        df.to_csv(path_or_buf=f"{RTDIR}/../data/permutations_{method}_{start_word}_full.csv", index=False)
        time_stop_word = datetime.datetime.now()
        rrow = np.array(row[1:])
        word_time = time_stop_word-time_start_word
        print(f"Took {word_time} seconds to process {start_word}")
        print(f"{start_word} scored an average of {rrow.mean()} and failed {len(failed)} times")

        row2 = [word_time, start_word, rrow.mean(), rrow.min(), rrow.max(), len(failed), failed]

        df2.loc[len(df2.index)] = row2

    time_stop_perm = datetime.datetime.now()
    print(f"Took {time_stop_perm-time_start_perm} seconds to complete the permutations")

    # df.sort_values(by=["Odds", ""], ascending=False, inplace=True, ignore_index=True)
    df2.sort_values(by=["Average Score", "Failure Count"], ascending=True, inplace=True, ignore_index=True)

    df2.to_csv(path_or_buf=f"{RTDIR}/../data/permutation_{method}_stats.csv", index=False)

    print(df2)


if __name__ == "__main__":
    t1 = SimPlayer()

    play()
    permutate

    # permutate(method='cum')
    # permutate(method='uni')
    # permutate(method='slo')
    # permutate(method='tot')
    # print(play(start="caste", solution="toxin", manual=True))
    # print(t1.play(start="flash", solution="mayor", manual=True, method='slo'))
    print(t1.play(start="flash", solution=None, manual=True, method='slo'))