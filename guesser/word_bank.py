""" @file word_bank.py
    @author Sean Duffie
    @brief This program is intended to automatically solve the NYT Wordle puzzle.

    More features will be added to this in the future, but for now it just reads guesses
    and filters from a wordbank of options

    TODO: calculate statistics on which letters are most valuable to identify
    TODO: Guessing logic for automatic picking
"""
import difflib
import os
import random

import pandas as pd

RTDIR = os.path.dirname(__file__)


METHODS = {
    "cum": 0,
    "uni": 1,
    "slo": 2,
    "tot": 3
}


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
        first_word (str): the word from the wordle database
        second_word (str): The regex pattern to compare it to
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
        # self.original_bank["Slot Odds"] = self.original_bank["Words"].apply(
            # func=self.solution_odds,
            # args=(slot_alpha,True)
        # )
        # self.original_bank.sort_values(
            # by=["Slot Odds"],
            # ascending=False,
            # inplace=True,
            # ignore_index=True
        # )
        # print(self.original_bank)

    def read_file(self):
        """ Reads in the word bank downloaded from the interned, then parses for only valid words

        Returns:
            pd.Dataframe: Single column Dataframe that has all possible 5 letter words
        """
        file = pd.read_csv(filepath_or_buffer=f'{RTDIR}\\..\\valid_guesses.csv', names=["Words"])
        return file

    def parse_submission(self, word: str, res: str):
        """ Extracts useful information from the submitted word and it's results.

        NOTE: Below are listed multiple cases that have to be handled when reading results
            Wordle already knows the answer, so they have a pool of correct characters.
            - First, the word is searched for letters in the correct spot. These are removed from
                the pool of correct characters and marked green (2).
            - Next, the word is scanned from left to right to see if each letter is in the pool of
                correct characters. For each correct character found, it is marked yellow (1) and
                then removed from the pool.
            - This means that if there are duplicate letters, only the correct one, or the first
                one will be marked. Any others will be rejected. (Examples below)
                - If the solution is "TUTOR":
                    - "STATE" will return "01010" because there are two "T"s in the pool
                    - "TASTE" will return "20010" because there is still a second "T" in the pool
                    - "RURAL" will return "12000" because only the first "R" is detected
                    - "ROWER" will return "01002" because only the correct "R" is detected

        Args:
            word (str): submitted guess
            res (str): results of guess
        """
        # User Input error handling assertions
        assert len(word) == 5
        assert len(res) == 5
        assert word.isalpha()
        assert res.isnumeric()
        self.guess_count += 1

        # Parse results and update letter information
        for i, letter in enumerate(word):
            if res[i] == "2":                           # RIGHT LETTER, RIGHT SPOT
                self.confirmed[i] = letter
                # If a duplicate letter is rejected earlier, then confirmed, remove from rejected.
                self.rejected[i].replace(letter, "")

            elif res[i] == "1":                         # RIGHT LETTER, WRONG SPOT
                self.rejected[i] += letter
                self.possible += letter

            elif res[i] == "0":                         # WRONG LETTER
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

    def search(self, word: str):
        """ Helper function to be applied on the wordbank dataframe

        TODO: Optimizations could be made here to make the search more accurate

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

    def eliminate(self):
        """ Remove words from the word_bank that don't match the pattern """
        # Generate a mask of the WordBank Dataframe by comparing the options with the known data
        before = len(self.word_bank["Words"])
        mask = self.word_bank["Words"].apply(self.search)
        # pattern = "..ing"
        # mask2 = self.word_bank["Words"].str.contains(pat=pattern, regex=True)
        # Apply the mask on the Dataframe and drop all False entries
        self.word_bank = self.word_bank[mask].reset_index(drop=True)
        after = len(self.word_bank["Words"])
        if self.debug:
            print(f"Before Drop: {before} | After Drop: {after}")

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
        else:
            # Total letters that were counted
            count = sum(alphabet.values())

        for i in range(5):
            letter = word[i]

            # If the letter is already confirmed, it shouldn't affect the odds
            if self.confirmed[i] == "":
                # If the statistics were gathered per slot, calculate accordingly
                if slot:
                    odds *= alphabet[i][letter] / count[i]
                else:
                    odds *= alphabet[letter] / count

        return odds

    def examine_options(self, method: int):
        """ Generate value of each word as a follow-up guess and sort based on method.

        Args:
            method (int): Which method should be used to calculate and sort the DataFrame.

        Returns:
            str: Word recommended from word_bank DataFrame.
        """
        # Calculate the probability of remaining options and append as a column (based on config)
        # TODO: This could be condensed if I got rid of "tot" (3) method
        tot_alpha, con_alpha, slot_alpha = self.generate_probs()
        if method in [0, 3]:
            self.word_bank["Cumul Odds"] = self.word_bank["Words"].apply(
                func=self.solution_odds,
                args=(tot_alpha,)
            )
        if method in [1, 3]:
            self.word_bank["Unique Odds"] = self.word_bank["Words"].apply(
                func=self.solution_odds,
                args=(con_alpha,)
            )
        if method in [2, 3]:
            self.word_bank["Slot Odds"] = self.word_bank["Words"].apply(
                func=self.solution_odds,
                args=(slot_alpha,True)
            )

        # If combining configurations, generate a new column will all other data
        if method == 3:
            def sum_cats(row):
                return row["Cumul Odds"] * row["Unique Odds"] * row["Slot Odds"]

            # Combine all of the odds
            self.word_bank["Total Odds"] = self.word_bank.apply(
                func=sum_cats,
                axis=1
            )

        # Sort the Dataframe based on configuration
        match method:
            case 0:
                self.word_bank.sort_values(
                    by=["Cumul Odds"],
                    ascending=False,
                    inplace=True,
                    ignore_index=True
                )
            case 1:
                self.word_bank.sort_values(
                    by=["Unique Odds"],
                    ascending=False,
                    inplace=True,
                    ignore_index=True
                )
            case 2:
                self.word_bank.sort_values(
                    by=["Slot Odds"],
                    ascending=False,
                    inplace=True,
                    ignore_index=True
                )
            case 3:
                self.word_bank.sort_values(
                    by=["Total Odds"],
                    ascending=False,
                    inplace=True,
                    ignore_index=True
                )
            case _:
                print("Invalid probability calculation configuration!")

        return self.word_bank["Words"][0]

    def submit_guess(self, word: str, res: str, method: str = 'slo') -> str:
        """ Update the database off of recent guess, then select the next most likely
        (or most productive) option to make progress

        Args:
            word (str): Guess that will be used to modify the word bank
            res (str): Results from the guess, 2 is correct, 1 is present, 0 is rejected
            method (str): What method should be used to sort for the next guess?

        Returns:
            str: recommended next guess based on probability algorithm
        """
        # Extract info from the submission
        self.parse_submission(word, res)

        # Eliminate invalid options from the word_bank dataframe
        self.eliminate()

        # Stop the guessing process if the database is empty (this should not happen)
        if self.word_bank["Words"].size == 0:
            if self.debug:
                print("Error! No more options!")
            return "failed"

        guess = self.examine_options(METHODS[method])

        alt = None
        guess = guess if alt is None else alt

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
            self.original_bank["Sim"] = self.original_bank["Words"].apply(
                func=find_bridge,
                args=(oddballs,)
            )

            # Drop values that don't score high enough
            index_sim = self.original_bank[(self.original_bank['Sim'] < 0.6)].index
            self.original_bank.drop(index_sim, inplace=True)

            # Sort the filtered results and reset the index
            self.original_bank.sort_values(
                by=["Sim"],
                ascending=False,
                inplace=True,
                ignore_index=True
            )
            self.original_bank = self.original_bank.reset_index(drop=True)

            # Return the most likely suggested word
            return self.original_bank["Words"][0]

        # Print results to user if they are actively participating
        if self.debug:
            print("\nRemaining:")
            print(self.word_bank)

        return guess

    def get_rand(self, orig: bool = True) -> str:
        """ Gets a random word from the selection

        Args:
            orig (bool, optional): Should it use the whole word bank selection? Defaults to True.

        Returns:
            str: The randomly chosen word.
        """
        if orig:
            return self.original_bank["Words"][random.randint(0, len(self.original_bank["Words"]))]
        return self.word_bank["Words"][random.randint(0, len(self.word_bank["Words"]))]

if __name__ == "__main__":
    # Generate the Wordbank object (This loads the dictionary list)
    wb = WordBank(debug=True)
    # wb.submit_guess(word="     ", res="00000", method="tot")
    # GUESS_COUNT = 1

    # # Enter each guess along with the results recieved from Wordle
    # # GUESS = input("Enter first guess: ")
    # GUESS = "crane"
    # # GUESS = input("Invalid entry! Can only be 5 characters and alphabetic! Try again: ")

    # start = datetime.datetime.now()
    # while GUESS != "q":
    #     # Prompt the user for what the results were
    #     RESULTS = input("What were the results? (2=green, 1=yellow, 0=grey) (ex. '02001'): ")

    #     # Check if the user won
    #     if RESULTS == "22222":
    #         print(f"\nCongrats! Wordle Solved in {GUESS_COUNT} attempts! Final Answer = {GUESS}")
    #         break

    #     # Check if the user exceeded the guess limit
    #     if GUESS_COUNT >= 6:
    #         print("\nSorry, you've used all of your guesses")
    #         break

    #     # Perform the actual check and suggest next words
    #     guess_response = wb.submit_guess(word=GUESS.lower(), res=RESULTS, method='tot')

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
