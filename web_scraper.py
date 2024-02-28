"""_summary_
    https://www.wordunscrambler.net/word-list/wordle-word-list
"""
import requests
from bs4 import BeautifulSoup

def scrape_website(url: str) -> requests.models.Response:
    response = requests.get(url)

    if response.status_code == 200:
        return response
    else:
        print('Failed to retrieve BBC News.')
        return(None)

def parse_html(html: requests.models.Response) -> list:
    # Create the HTML Text Parser
    soup = BeautifulSoup(html.text, 'html.parser')
    # Find all links that contain an href
    links = soup.find_all('a', href=True)

    # For each link, check whether it contains a Wordle option
    option_list = []
    for link in links:
        if "/unscramble/" in link['href']:
            option_list.append(link.text)

    return option_list

if __name__ == "__main__":
    URL = 'https://www.wordunscrambler.net/word-list/wordle-word-list'
    HTML = scrape_website(url=URL)
    parse_html(html=HTML)
