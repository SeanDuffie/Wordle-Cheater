""" @file
    @author Sean Duffie
    @brief


"""
import time

import selenium.webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from word_bank import WordBank
from typing import Generator


class RealPlayer():
    """ RealPlayer is a slightly more advanced webscraper than my previous one.

        This object will allow the user to launch a simulated test browser in chrome,
        click buttons, and then send keypresses to simulate entering words. This will
        also allow the user to query the results of each guess from the NYT webpage.

        This object is also designed to play nicely with both the WordBank object and
        the DiscordBot interfaces.
    """
    def __init__(self, url: str):
        # Launch the Chrome browser
        # NOTE: This was working on one computer but not another. Adding the ChromeDriverManager seemed to fix it, but I'm still cautious.
        # FIXME: This line behaves differently on different versions of python
        # Python 3.12
        self.driver = selenium.webdriver.Chrome()
        # Python 3.10
        # self.driver = selenium.webdriver.Chrome(executable_path=ChromeDriverManager().install())
        # navigate to the login page
        self.driver.get(url=url)
        # Set up an Action Handler for sending keypresses
        self.actions = ActionChains(driver=self.driver)

        # locate the "Play" button by its text and click on it.
        self.select_button(By.XPATH, "//button[contains(text(),'Play')]")
        # Close out the tutorial window by selecting the "X" icon.
        self.select_button(By.CLASS_NAME, "Modal-module_closeIcon__TcEKb")
        time.sleep(.4)

        self.counter = 0

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.driver.close()
        self.driver.quit()

    def select_button(self, method: str, value: str) -> None:
        """ Click an element on the webpage

        Used to locate and close dialog/tutorial boxes when they pop up.

        Args:
            method (str): What method to use to find it? Class name, xpath, id, etc.
            value (str): What is the value to search for?
        """
        self.driver.find_element(by=method, value=value).click()
        time.sleep(.1)

    def play_word(self, word: str) -> str:
        """ Plays a word on the NYT Wordle webpage by typing it.

        Args:
            word (str): What word to play?

        Returns:
            str: Results of that word from the site itself
        """
        # Handle going over the guess limit
        if self.counter >= 6:
            # Instead of returning nothing, we will go over the guess limit by one to get the actual answer
            result = self.driver.find_element(by=By.XPATH, value='//*[@id="ToastContainer-module_gameToaster__HPkaC"]/div').text.lower()
        else:
            # Send the keypresses to the webpage
            self.actions.send_keys(word + "\n")
            self.actions.perform()

            # Give enough time for the animation to finish, then read the results
            time.sleep(2)
            result = self.read_results(self.counter)

            # Increment guess counter
            self.counter += 1

        return result

    def read_results(self, row: int) -> str:
        """ Read the results by scanning the table

        FIXME: Handle if user requests a row that is not populated yet
            - Try/except?
            - What to return?
            - 

        Args:
            row (int): Which row should you read? (This won't work if there are no results yet)

        Returns:
            str: The results parsed into a WordBank friendly string
        """
        result = ""
        div_list = self.driver.find_elements(by=By.CLASS_NAME, value="Tile-module_tile__UWEHN")

        for i in range(5):
            index = row * 5 + i
            num, let, res = div_list[index].get_attribute("aria-label").split(sep=", ")

            match res:
                case "absent":
                    result += "0"
                case "present in another position":
                    result += "1"
                case "correct":
                    result += "2"

        return result

    def run_generator(self) -> Generator[tuple[str, str], None, None]:
        """ Main runner for RealPlayer """
        wb = WordBank()
        guess = "flash"

        while True:
            try:
                result = self.play_word(guess)

                if result == "22222":
                    return (guess, result)

                yield (guess, result)

                guess = wb.submit_guess(word=guess, res=result, method="slo")
            except AssertionError as e:
                if guess.lower() == "failed":
                    print("Error! Ran out of options! (This shouldn't be possible)")
                    return (guess, result)
                # logger.error(e)
                print(e)
                print("Invalid Guess!")
                print(guess)

def run():
    """ Main runner for RealPlayer """
    url = "https://www.nytimes.com/games/wordle/index.html"
    wb = WordBank()
    guess = "flash"
    history = []

    with RealPlayer(url=url) as player:
        while True:
            result = player.play_word(guess)
            history.append((guess, result))
            print(history)

            if result == "22222":
                break

            try:
                guess = wb.submit_guess(word=guess, res=result, method="slo")
            except AssertionError as e:
                if guess.lower() == "failed":
                    print("Error! Ran out of options! (This shouldn't be possible)")
                    break
                # logger.error(e)
                print(e)
                print("Invalid Guess!")
                print(guess)

    return history

if __name__ == "__main__":
    url = "https://www.nytimes.com/games/wordle/index.html"
    with RealPlayer(url) as rp:
        for item in rp.run_generator():
            print(item)

    print("\n\nTAKE TWO:")
    run()
