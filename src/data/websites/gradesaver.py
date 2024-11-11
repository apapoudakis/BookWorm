from string import ascii_uppercase
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def scrape():
    """Scrape url links of GradeSaver website"""

    base_url = "https://www.gradesaver.com/"
    studies_url = f"{base_url}study-guides/"
    lit_titles = []
    lit_authors = []
    lit_websites = []

    for letter in ascii_uppercase:
        page = requests.get(studies_url + letter)
        soup = BeautifulSoup(page.content, "html.parser")
        lit_studies = soup.find_all("a", class_="columnList__link")
        for x in lit_studies:
            title = x.text.strip()
            url = urljoin(base_url, x["href"])

            lit_titles.append(title)
            lit_authors.append(x.findNext("a").text)
            lit_websites.append(url)

    return lit_titles, lit_authors, lit_websites


def get_data(book_id, title, author, url, data_type):
    """
    Scrape characters description, analysis or book summary
    """

    if data_type == "description":
        descr_url = url + "/" + "study-guide/character-list"
        return get_character_description(book_id, title, author, descr_url)
    elif data_type == "summary":
        return get_summary(url)
    else:
        raise ValueError(f"Unknown data_type: {data_type}")


def get_character_description(book_id, title, author, url):
    """Retrieve character descriptions from the specified URL."""

    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    chars_nodes = soup.find_all("h2", class_="toc_header")
    data = []

    for c_node in chars_nodes:
        char_name = c_node.text.strip().replace(":", "")
        descr = c_node.findNext("p").text.strip()
        data.append(
            {"id": book_id, "book": title, "author": author, "character": char_name,
             "description": descr, "source": "GradeSaver", "url": url})

    return data


def get_summary(url):
    """Retrieve the book summary from the specified URL."""

    url_suffix = "/study-guide/summary"

    page = requests.get(url + "/" + url_suffix)
    soup = BeautifulSoup(page.content, "html.parser")
    summary_paragraphs = []

    article_node = soup.find("article", class_="section__article")

    if article_node:
        paragraphs = article_node.find_all("p")
        for p in paragraphs:
            summary_paragraphs.append(p.text.strip())

    summary = "\n\n".join(summary_paragraphs)

    return summary


if __name__ == "__main__":
    output = get_data(3694, "Every Man in His Humour", "Ben Jonson",
                                                       "https://web.archive.org/web/20230330202918/https://www"
                                                       ".gradesaver.com/every-man-in-his-humour/",
                                                       "description")
    print(output)
