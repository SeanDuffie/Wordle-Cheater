"""_summary_
    https://www.wordunscrambler.net/word-list/wordle-word-list
"""
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup

RTDIR = os.path.dirname(__file__)

def scrape_website(url: str) -> BeautifulSoup:
    """_summary_

    Args:
        url (str): _description_

    Returns:
        requests.models.Response: _description_
    """
    # Perform the request
    response = requests.get(url=url, timeout=10)

    # Check if the HTTP request was successful
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print('Failed to retrieve HTML.')
        return None

def parse_html(soup: BeautifulSoup) -> pd.Series:
    """_summary_

    Args:
        html (requests.models.Response): _description_

    Returns:
        pd.Series: _description_
    """
    # Find all links that contain an href
    links = soup.find_all('a', href=True)

    # For each link, check whether it contains a Wordle option
    option_list = []
    for link in links:
        if "/unscramble/" in link['href']:
            # option_list.append(link.text)
            option_list.append(link.text)

    options = pd.Series(option_list)
    return options


def parse_table(soup: BeautifulSoup) -> pd.DataFrame:
    """_summary_

    Args:
        html (requests.models.Response): _description_

    Returns:
        pd.Series: _description_
    """
    tbl = soup.find("table")
    df = pd.read_html(str(tbl))[0]

    return df

if __name__ == "__main__":
    URL = 'https://www.wordunscrambler.net/word-list/wordle-word-list'
    HTML = scrape_website(url=URL)
    db = parse_html(soup=HTML)
    # db.to_csv(path_or_buf=f"{RTDIR}/words.csv", index=False, header=False)
    print(db)
    
    URL2 = "https://www.zippia.com/advice/average-cost-of-groceries-by-state/"
    HTML2 = scrape_website(url=URL2)
    db2 = parse_table(soup=HTML2)
    # db2.to_csv(path_or_buf=f"{RTDIR}/groceries.csv", index=False, header=False)
    print(db2)
