"""_summary_
    https://www.wordunscrambler.net/word-list/wordle-word-list
"""
import requests
from bs4 import BeautifulSoup

def scrape_website(url):
    response = requests.get(url)

    if response.status_code == 200:
        print(type(response))
        return response
    else:
        print('Failed to retrieve BBC News.')
        return(None)
    
def parse_html(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    headlines = soup.find_all('h3', class_='list-header')

    for headline in headlines:
        # headline_text = headline.text.strip()
        print(headline.text.strip())
        marker = headline
        while marker is not None:
            marker = marker.find_next('a')
            print(marker.text)

if __name__ == "__main__":
    URL = 'https://www.wordunscrambler.net/word-list/wordle-word-list'
    HTML = scrape_website(url=URL)
    parse_html(html=HTML)
    
