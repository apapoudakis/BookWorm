import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.utils.misc import check_snapshot_date


def scrape():
    """Scrape url links of Shmoop website"""

    base_page = "https://web.archive.org/web/20230330202918/https://www.shmoop.com/study-guides/literature/index/?p="
    num_pages = 96

    lit_titles = []
    lit_authors = []
    lit_websites = []

    for i in range(1, num_pages+1):
        page = requests.get(base_page + str(i))
        soup = BeautifulSoup(page.content, "html.parser")
        lit_studies = soup.find_all("a", class_="details")

        page_titles = [
            item.find("div", class_="item-info").get_text(strip=True) for item in lit_studies
        ]
        page_urls = [item["href"] for item in lit_studies]

        lit_titles.extend(page_titles)
        lit_authors.extend(["N/A"] * len(page_titles))  # no available author name
        lit_websites.extend(page_urls)
        print(f"Page {i}: {page_urls}")

    return lit_titles, lit_authors, lit_websites


def get_data(book_id, title, author, url, data_type, max_attempts=3, sleep_time=30):
    """
    Scrape characters description and book summary
    """

    if data_type == "analysis":
        url_suffix = "/characters/"
        c_url = url + url_suffix

        char_urls, char_names = extract_char_analysis_urls(c_url)
        url_to_data = {}
        for i, _url in enumerate(char_urls):
            attempt = 0
            while attempt < max_attempts:

                try:
                    _data = get_character_analysis(book_id, title, author, _url, char_names[i])
                    if _data:
                        url_to_data[_url] = _data
                        break
                    time.sleep(30)
                except Exception as e:
                    # print(e)
                    pass

                if attempt < max_attempts:
                    time.sleep(sleep_time)
                    attempt += 1

        flattened_char_analysis = [item for sublist in url_to_data.values() for item in sublist]

        return flattened_char_analysis

    elif data_type == "summary":
        return get_summary(url)
    else:
        raise ValueError("Invalid data_type. Expected 'analysis' or 'summary'.")


def extract_char_analysis_urls(url):
    """
    Extract character analysis URLs from the characters page.
    """
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    nodes = soup.find("div", attrs={'data-content-type': 'text'})
    character_analysis_urls = []
    char_names = []
    base_url = urlparse(url).netloc

    if nodes:
        for n in nodes:
            if n.find("a"):
                char_name = n.text.strip()
                char_names.append(char_name)
                url_suffix = n.find("a")["href"]
                char_url = "https://" + base_url + url_suffix

                if char_url not in character_analysis_urls:
                    character_analysis_urls.append(char_url)

    return character_analysis_urls, char_names


def get_character_analysis(book_id, title, author, url, char_name=None):
    """
    Scrape character analysis from a given url
    """
    data = []
    page = requests.get(url)
    valid, edit_page = check_snapshot_date(page, url)
    if not valid:
        page = edit_page

    soup = BeautifulSoup(page.content, "html.parser")

    analysis = ""
    title_node = soup.find("h2", class_="title")
    if title_node:
        siblings = title_node.find_next_siblings(["h3", "p"])
        for s in siblings:
            analysis += re.sub("\s+", " ", s.text).strip() + "\n\n"

        data.append(
            {"id": book_id, "book": title, "author": author, "character": char_name,
             "analysis": analysis.strip(),
             "source": "Shmoop", "url": url})

    return data


def get_summary(url):
    """
    Scrape the summary from a given URL
    """

    summary_url = f"{url}/summary"

    page = requests.get(summary_url)
    soup = BeautifulSoup(page.content, "html.parser")
    summary_paragraphs = []
    node = soup.find("h2", class_="title")

    if node:
        for s in node.find_next_siblings(["p", "h2", "h3"]):
            summary_paragraphs.append(s.text.replace("\n", " "))

        summary = "\n\n".join(summary_paragraphs)
    else:
        summary = ""

    return summary


if __name__ == "__main__":

    output = get_data(9701, "Beowulf", "",
                      "https://web.archive.org/web/20220819113154/https://www.shmoop.com/study-guides/literature"
                      "/beowulf",
                      "analysis")
    print(output)
