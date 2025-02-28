import json
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
import time


def scrape():
    """Scrape url links of LitCharts website"""

    base_url = "https://www.litcharts.com/"
    all_studies_url = f"{base_url}lit#all"
    page = requests.get(all_studies_url)
    soup = BeautifulSoup(page.content, "html.parser")

    lit_studies = soup.find("div", id="all")
    all_lits = json.loads(lit_studies.find("div")["data-react-props"])

    lit_titles = []
    lit_authors = []
    lit_websites = []

    for i in all_lits["guides"]:
        lit_titles.append(i["title"])
        lit_authors.append(i["author_name"])
        lit_websites.append(urljoin(base_url, i["url"]))

    return lit_titles, lit_authors, lit_websites


def get_data(book_id, title, author, url, data_type):
    """
    Scrape characters description and book summary
    """

    if data_type == "description":
        return get_character_description(book_id, title, author, url)
    elif data_type == "summary":
        return get_summary(url)
    else:
        raise ValueError(f"Invalid data_type: {data_type}")


def get_character_description(book_id, title, author, url, max_attempts=3):
    """
    Scrape character descriptions for a given url
    """

    url_suffix = "characters/"
    base_url = urlparse(url).netloc
    data = []
    scrape_url = urljoin(url + "/", url_suffix)

    page = requests.get(scrape_url)
    soup = BeautifulSoup(page.content, "html.parser")

    chars_node = soup.find_all("a", class_="subcomponent tappable", string="All Characters")

    if chars_node:
        chars = chars_node[0].findNextSiblings("a", class_="subcomponent tappable")
        for c in chars:
            # print(c)
            num_attempts = 0

            # max_retries per character
            # Keep trying until success or until we exceed max_retries
            while num_attempts < max_attempts:

                try:
                    char_name = c.text.strip()
                    character_url = "https://" + base_url + c["href"]
                    char_response = requests.get(character_url)
                    char_soup = BeautifulSoup(char_response.content, "html.parser")
                    description_node = char_soup.find_all("div", class_="highlightable-content")

                    if description_node:
                        descr = description_node[0].text.strip()

                        data.append(
                            {"id": book_id, "book": title, "author": author, "character": char_name, "description": descr,
                             "source": "LitCharts", "url": character_url})
                        break
                except:
                    print("wait")
                    time.sleep(30)

                    if num_attempts == max_attempts:
                        raise ValueError("Failed to scrape character description")

                num_attempts += 1

    return data


def get_summary(url):
    """Scrape the summary of the book from the given URL."""

    url_suffix = "summary"
    page = requests.get(url + "/" + url_suffix)
    soup = BeautifulSoup(page.content, "html.parser")

    paragraphs = soup.find_all("p", class_="plot-text")
    summary_paragraphs = []
    for p in paragraphs:
        summary_paragraphs.append(p.text.lstrip())

    summary = "\n\n".join(summary_paragraphs)

    return summary


if __name__ == "__main__":

    output = get_data(1792, "Measure for Measure", "William Shakespeare",
                      "https://web.archive.org/web/20231207174120/https://www.litcharts.com/lit/measure-for-measure",
                      "description")
