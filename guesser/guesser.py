""" @file guesser.py
    @author Sean Duffie
    @brief This program is intended to automatically solve the NYT Wordle puzzle.

    More features will be added to this in the future, but for now it just reads guesses
    and filters from a wordbank of options
    
    TODO: calculate statistics on which letters are most valuable to identify
    TODO: Guessing logic for automatic picking
"""
import pandas as pd


class WordBank:
    """ The WordBank object represents all possible Wordle options
        as they narrow down with more guesses.
    """
    def __init__(self):
        all_words = self.read_file()
        self.narrowed = all_words.copy()

        # When a letter is confirmed to a location (GREEN), it will be placed here
        self.confirmed = ["", "", "", "", ""]
        # When a letter is rejected (GREY OR YELLOW AT LOCATION), it will be placed here
        self.rejected = ["", "", "", "", ""]
        # If a letter is identified, but location is unknown (YELLOW), it will be placed here
        self.possible = ""

    def read_file(self):
        """ Reads in the word bank downloaded from the interned, then parses for only valid words
        
        TODO: Output the filtered file to save overhead time in the future
        FIXME: This contains many words that either aren't real or don't exist in Wordle database

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

        file = pd.read_table(filepath_or_buffer='words.txt', names=["Words"])
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
        # print(f"{self.confirmed=}\n{self.rejected=}\n{self.possible=}")

        # Generate a mask of the WordBank Dataframe by comparing the options with the known data
        mask = self.narrowed["Words"].apply(self.search)
        # Apply the mask on the Dataframe and drop all False entries
        self.narrowed = self.narrowed[mask].reset_index(drop=True)

        print("New Options Generated:")
        print(self.narrowed)

    def search(self, word):
        """ Helper function to be applied on the wordbank dataframe

        TODO: Optimizations could be made here to make the search more accurate

        Args:
            word (str): input string that is being compared

        Returns:
            bool: True if the word is a possible combination of letters
        """
        for i in range(5):
            if self.confirmed[i] != "":
                if word[i] != self.confirmed[i]:
                    return False
            if word[i] in self.rejected[i]:
                return False
        return True


if __name__ == "__main__":
    # Generate the Wordbank object (This loads the dictionary list)
    b = WordBank()

    # Enter each guess along with the results recieved from Wordle
    GUESS = "aegis"
    while GUESS != "q":
        RESULTS = input("What were the results? (2=green, 1=yellow, 0=grey) (ex. '02001'): ")
        b.check(GUESS, RESULTS)
        GUESS = input("Enter next guess (or 'q' to quit): ")
