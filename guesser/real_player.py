""" @file
    @author Sean Duffie
    @brief


"""
import time

import selenium.webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


class RealPlayer():
    """_summary_
    """
    def __init__(self, url: str):
        # Launch the Chrome browser
        self.driver = selenium.webdriver.Chrome()
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

    def select_button(self, method: str, value: str):
        self.driver.find_element(by=method, value=value).click()
        time.sleep(.1)

    def play_word(self, word: str):
        if self.counter >= 6:
            print("Over Guess Limit")
            # yield "loser"
        else:
            print(f"Sending word: {word}")

        self.actions.send_keys(word + "\n")
        self.actions.perform()

        # TODO: yield results
        time.sleep(2)
        result = self.read_results(self.counter)

        # Increment
        self.counter += 1

        return result

    def read_results(self, row: int):
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

if __name__ == "__main__":
    URL = "https://www.nytimes.com/games/wordle/index.html"

    with RealPlayer(URL) as player:
        # Wait for the page to load and animations to finish, then
        print(player.play_word("flash"))
        print(player.play_word("flash"))
        print(player.play_word("flash"))
        print(player.play_word("flash"))
        print(player.play_word("flash"))
        print(player.play_word("flash"))

        # TODO: if failed, read the correct answer
        time.sleep(3)

    print("Done")
