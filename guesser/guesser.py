"""_summary_
"""
alphabet = "abcdefghijklmnopqrstuvwxyz"
special_characters = "\"\'\\!@#$%^&*()-+?_=,.<>/"

def no_special(st: str):
    for s in st:
        if s in special_characters:
            return False
    return True


class WordBank:
    def __init__(self):
        with open('words.txt') as word_file:
            ency = word_file.read().split()
            wordle = [st.lower() for st in ency if (len(st) == 5 and no_special(st))]
            # print(wordle)
            # print(f"Number of 5 letter words: {len(wordle)}")

    def check(self, word: str) -> bool:
        return True

class Guesser:
    def __init__(self, first: str):
        bank = WordBank()
        self.guesses = [first]
        self.possible_letters = alphabet
        self.identified_letters = ""
        self.rejected_letters = ["", "", "", "", ""]
        self.confirmed_letters = ["", "", "", "", ""]

        c = 0
        looping = True
        while looping:
            self.guesses.append(self.generate_guess())
            print(f"{self.guesses=}")
            print(f"{self.rejected_letters=}")
            print(f"{self.confirmed_letters=}")
            self.submit(self.guesses[len(self.guesses)-1], [0,0,0,0,0])

            looping = False
            for s in self.confirmed_letters:
                if s == "":
                    looping = True

        self.guesses[1] = input("Enter the 5 letter word for second guess")

    def generate_guess(self):
        return input("Enter next guess: ")

    def submit(self, word, results):
        for i in range(len(word)):
            match results[i]:
                case 0:
                    self.possible_letters.replace(word[i], "")
                    for l in range(5):
                        self.rejected_letters[l] += word[i]
                case 1:
                    self.rejected_letters[i] = word[i]
                    self.identified_letters += word[i]
                case 2:
                    self.confirmed_letters[i] = word[i]

if __name__ == "__main__":
    # g = Guesser()
    # g.check("word")
    Guesser("aegis")
