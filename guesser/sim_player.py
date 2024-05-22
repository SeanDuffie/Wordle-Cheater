""" @file sim_player.py
    @author Sean Duffie
    @brief Simulates a Wordle player with a known input.

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
OPTIONS = WordBank().original_bank["Words"].tolist()


class SimPlayer:
    """ SimPlayer will be what gathers the statistical data from performance testing
    """
    def __init__(self, solution: str = None, first: str = "flash", method: str = "slo", manual: bool = False) -> None:
        self.wb = WordBank(debug=manual)

        if solution == "rand":
            solution = self.wb.get_rand()

        if solution is not None:
            assert len(solution) == 5
            assert solution.isalpha()
            assert solution in OPTIONS
        self.solution = solution

        # TODO: Should guesses be stored inside of the object instead of in the generator call?
        assert len(first) == 5
        assert first.isalpha()
        assert first in OPTIONS
        self.guess = first

        assert method in ["cum", "uni", "slo", "tot"]
        self.method = method

        # TODO: Add manual boolean here?

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        pass

    def read_results(self, guess: str) -> str:
        """ Generates a 'results' string from a guess when the solution is known

        Args:
            guess (str): the user or system generated guess

        Returns:
            str: Formatted results string that compares the solution with the guess
        """
        # Must keep local copy of solution for each read since it will be overwritten with spaces.
        solution = self.solution
        result = "00000"

        # print(f"{guess=}, {solution=}")
        # First, eliminate all letters known to be correct, mask the correct letters with whitespace
        for i in range(5):
            if guess[i] == solution[i]:
                # print(f"{guess[i]} == {solution[i]} -> '2'")
                result = result[:i] + "2" + result[i+1:]
                guess = guess[:i] + " " + guess[i+1:]
                solution = solution[:i] + " " + solution[i+1:]

        # Next, identify all the characters that are present but not in the correct spot
        # Doing it this way allows you to identify duplicate letters without looping on confirmed
        # Additionally, only one "possible" duplicate letter should be marked for each duplicate
        for i in range(5):
            if guess[i] != " ":
                if guess[i] in solution:
                    result = result[:i] + "1" + result[i+1:]

                    # Replace the character in solution with whitespace to handle duplicates
                    j = solution.index(guess[i])
                    solution = solution[:j] + " " + solution[j+1:]
                #     print(f"{guess[i]} is in {solution} -> '1'")
                # else:
                #     print(f"{guess[i]} is not in {solution} -> 0")

        return result

    def update_method(self, method: Literal['cum', 'uni', 'slo', 'tot'] = None) -> None:
        """ Main runner for RealPlayer """
        if method is not None:
            assert method in ["cum", "uni", "slo", "tot"]
            self.method = method

    def run_generator(self) -> Generator[Tuple[str, str], None, None]:
        """ Plays the Wordle one at a time.
        
        This is a more efficient solution for interfacing with other code or being flexible.
        This will also help to run multiple instances at once and store them for the discord bot.

        Yields:
            Generator[Tuple[str, str], None, None]: Generator called for every attempt.
        """
        # assert len(guess) == 5
        # assert guess.isalpha()
        # assert guess in OPTIONS

        while True:
            try:
                # If the solution is unknown, prompt user for results, otherwise generate them
                if self.solution is None:
                    result = get_valid_results(guess=self.guess)
                else:
                    # Submit guess, then yield results
                    result = self.read_results(guess=self.guess)

                # Get suggestion from the wordbank for the next guess
                print(f"Submitting guess: {self.guess} (results: {result})")
                next_guess = self.wb.submit_guess(word=self.guess, res=result, method="slo")

                # Yield Generator output
                response = yield self.guess, result

                # Process response, if None then use default
                if response is None:
                    self.guess = next_guess
                else:
                    self.guess =  response
                    yield self.guess

                # Check victory conditions, or if out of guesses, get the final result
                if result == "22222" or result.isalpha():
                    return

            except AssertionError:
                if self.guess.lower() == "failed":
                    print("Error! Word Bank ran out of options! (This shouldn't be possible)")
                    return
                print(f"Invalid Guess: {self.guess}")

def get_valid_results(guess):
    """ Gets valid result string from user terminal input. Loops on error to avoid need to restart.

    Args:
        guess (str): What is the word that is being guessed? This is mainly for user experience.

    Raises:
        ValueError: Raises an error if the input is the wrong length.
        ValueError: Raises an error if the input contains invalid characters.
        ValueError: Raises an error if the input contains invalid numbers.

    Returns:
        str: The string format of results accepted by WordBank().
    """
    while True:
        try:
            result = input(f"What were the results for '{guess}'? (2=green, 1=yellow, 0=grey): ")
            if not len(result) == 5:
                raise ValueError("Invalid Result size, must be 5 digits..")
            if not result.isnumeric():
                raise ValueError("Result must be numerical (no special or letters).")
            if any(inv_num in result for inv_num in ['3', '4', '5', '6', '7', '8', '9']):
                raise ValueError("Result can only contain [0, 1, 2].")
            break
        except ValueError as e:
            print(e)
            # logger.error(e)
    return result

def get_valid_guess():
    """ Gets a valid guess from user terminal input. Loops on error to avoid need for restart.

    Raises:
        ValueError: Raises an error if the input is the wrong length.
        ValueError: Raises an error if the input contains invalid characters.
        ValueError: Raises an error if the string is not contained within the list of options.

    Returns:
        str: The acquired word input (after being checked for validity).
    """
    while True:
        try:
            guess = input("Enter guess: ")
            if not len(guess) == 5:
                raise ValueError("Word must be 5 letters long. Try Again.")
            if not guess.isalpha():
                raise ValueError("Guess must be alphabetical (no special or numbers).")
            if guess not in OPTIONS:
                print(OPTIONS)
                raise ValueError("Word guess must be in the Wordle database.")
            break
        except ValueError as e:
            print(e)
            # logger.error(e)
    return guess

# TODO: This may need to become a generator eventually for the discord bot
# TODO: Eventually change the typehinting for method to a more sophisticated typehint method
def play(start: str = None, solution: str = None, method: str = 'slo', manual: bool = False):
    """ Controls the actual play process of the game

    Args:
        start (str, optional): What should the first guess be? Defaults to "crane".
        solution (str, optional): What is the solution? (For simulation purposes) Defaults to None.
        manual (bool, optional): Solve it manually or automatically? Defaults to False.
    """
    # Initialize list of guesses and first guess
    guesses = []
    if start is None:
        if manual:
            guess = get_valid_guess()
        else:
            guess = "flash"
    else:
        guess = start

    # If the solution is not defined, generate a random one
    if solution == "rand":
        wb = WordBank(debug=manual)
        solution = wb.word_bank["Words"][random.randint(0,len(wb.word_bank["Words"]))]

    # NOTE: When yielding from a generator, calling send() will also yield an output to be handled.
    with SimPlayer(solution=solution, method=method, manual=manual) as player:
        generator = player.run_generator()

        for guess, result in generator:
            # Log result history
            guesses.append((guess, result))

            # Check for victory conditions
            if result == "22222":
                print("Victory!")
                break

            if manual:
                new_guess = get_valid_guess()
                # Sends manual guess to the generator (Must be handled, yields a result)
                generator.send(new_guess)

            # Check to make sure that the dataframe didn't run out of choices
            if guess.lower() == "failed":
                print("Error! Ran out of options! (This shouldn't be possible)")
                break

    print(f"{guesses}")
    return guesses

def permutate(method: Literal['cum', 'uni', 'slo', 'tot'] = 'tot'):
    """ Runs through all the permutations of starting word compared to solution

        All other logic should be handled in the WordBank class
        TODO: Add multiprocessing here for faster runtimes
    """
    permutations_df = pd.DataFrame(
        columns=[
            "Time",
            "Start",
            "Average Score",
            "Min Score",
            "Max Score",
            "Failure Count",
            "Failures"
        ]
    )

    # Loop through all starting words
    time_start_perm = datetime.datetime.now()
    for start_word in ['flash']: # OPTIONS: # ['flash', 'caste', 'crane', 'worst']: #
        start_word_df = pd.DataFrame(columns=["Word", "Count"])
        # TODO: Add multiprocessing here
        row = [start_word]
        failed = []

        time_start_word = datetime.datetime.now()
        # Loop through all potential solutions
        for solution in OPTIONS:
            guesses = play(start=start_word, solution=solution, manual=False, method=method)

            row.append(len(guesses))
            start_word_df.loc[len(start_word_df.index)] = [solution, len(guesses)]

            if len(guesses) > 6:
                failed.append((solution, len(guesses), guesses))

        # Output to CSV
        start_word_df.to_csv(
            path_or_buf=f"{RTDIR}/../data/permutations_{method}_{start_word}_full.csv",
            index=False
        )

        # Calculate times
        time_stop_word = datetime.datetime.now()
        rrow = np.array(row[1:])
        word_time = time_stop_word-time_start_word
        print(f"Took {word_time} seconds to process {start_word}")
        print(f"{start_word} scored an average of {rrow.mean()} and failed {len(failed)} times")

        # Append row to permutations DataFrame
        row2 = [word_time, start_word, rrow.mean(), rrow.min(), rrow.max(), len(failed), failed]
        permutations_df.loc[len(permutations_df.index)] = row2

    # Calculate total time for permutations
    time_stop_perm = datetime.datetime.now()
    print(f"Took {time_stop_perm-time_start_perm} seconds to complete the permutations")

    # start_word_df.sort_values(by=["Odds", ""], ascending=False, inplace=True, ignore_index=True)
    permutations_df.sort_values(
        by=["Average Score", "Failure Count"],
        ascending=True,
        inplace=True,
        ignore_index=True
    )
    permutations_df.to_csv(
        path_or_buf=f"{RTDIR}/../data/permutation_{method}_stats.csv",
        index=False
    )
    print(permutations_df)


if __name__ == "__main__":
    # permutate(method='cum')
    # permutate(method='uni')
    # permutate(method='slo')
    # permutate(method='tot')

    # play(start="caste", solution="toxin", manual=True)
    # play(start="flash", solution="mayor", manual=True)
    play(start="flash", solution=None, manual=True)
