"""_summary_
    https://www.wordunscrambler.net/word-list/wordle-word-list
"""
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup

RTDIR = os.path.dirname(__file__)

def scrape_website(url: str) -> requests.models.Response:
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
        return response
    else:
        print('Failed to retrieve HTML.')
        return None

def parse_html(html: requests.models.Response) -> pd.Series:
    """_summary_

    Args:
        html (requests.models.Response): _description_

    Returns:
        pd.Series: _description_
    """
    # Create the HTML Text Parser
    soup = BeautifulSoup(html.text, 'html.parser')
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

if __name__ == "__main__":
    URL = 'https://www.wordunscrambler.net/word-list/wordle-word-list'
    HTML = scrape_website(url=URL)
    db = parse_html(html=HTML)
    db.to_csv(path_or_buf=f"{RTDIR}/words.csv", index=False, header=False)
    print(db)
