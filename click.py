""" @file
    @author Sean Duffie
    @brief


"""
# import necessary modules
import selenium.webdriver
from selenium.webdriver.common.by import By
import time
import pyautogui as pg

# create a new instance of the Firefox driver
driver = selenium.webdriver.Chrome()

# navigate to the login page
driver.get("https://www.nytimes.com/games/wordle/index.html")

# locate the "Sign In" button by its text and click on it
# driver.find_element(by=By.CLASS_NAME, value="Welcome-module_button__ZG0Zh").click()
driver.find_element(by=By.XPATH, value="//button[contains(text(),'Play')]").click()
time.sleep(.1)
driver.find_element(by=By.CLASS_NAME, value="Modal-module_closeIcon__TcEKb").click()

time.sleep(.5)

# inputElement = driver.find_element_by_id("a1")
# inputElement.send_keys('1')

pg.press("a")
pg.press("s")
pg.press("p")
pg.press("e")
pg.press("n")

pg.press("\n")

while True:
    pass
