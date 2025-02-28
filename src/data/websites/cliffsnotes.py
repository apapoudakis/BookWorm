import re
import time
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from src.utils.misc import check_snapshot_date


def scrape():
    """Scrape url links of Cliffnotes website"""

    base_url = "https://www.cliffsnotes.com/"
    all_literature_notes = "https://www.cliffsnotes.com/literature?filter=ShowAll&sort=TITLE"
    page = requests.get(all_literature_notes)
    soup = BeautifulSoup(page.content, "html.parser")

    lit_studies = soup.find_all("a", class_="clear-padding")
    lit_titles = []
    lit_authors = []
    lit_websites = []

    for lit_study in lit_studies:
        lit_titles.append(lit_study.find("h4").text)
        if lit_study.find("p").text:
            lit_authors.append(lit_study.find("p").text)
        else:
            lit_authors.append("N/A")
        lit_websites.append(urljoin(base_url, lit_study["href"]))

    return lit_titles, lit_authors, lit_websites


def get_data(book_id, title, author, url, data_type):
    """
    Scrape character description, analysis or book summary
    """

    if data_type == "description":
        description_link = urljoin(url[:url.rfind('/') + 1], "character-list")
        return get_character_description(book_id, title, author, description_link)
    elif data_type == "analysis":
        char_urls = extract_char_analysis_urls(url)
        char_analysis = []
        for _url in char_urls:
            char_analysis.extend(get_character_analysis(book_id, title, author, _url))
        return char_analysis
    elif data_type == "summary":
        return get_summary(url)
    else:
        raise ValueError(f"Unknown data_type: {data_type}")


def get_summary(url):
    """
    Scrape the summary from a given URL
    """
    url_suffix = ["/book-summary", "/play-summary", "/poem-summary"]
    summary = ""
    page = None
    for suffix in url_suffix:
        test_url = urljoin(url[:url.rfind('/') + 1], suffix)
        if requests.get(test_url):
            page = requests.get(test_url)
            break
    if page is None:
        page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    content_div = soup.find("div", class_="gts-placeholder-wrapper float left middle-for-small-only")

    if content_div:
        paragraphs = content_div.find_all_next("p", class_="litNoteText")
        for p in paragraphs:
            summary += p.text.strip() + "\n\n"

    return summary


def get_character_description(book_id, title, author, url, max_attempts=5):
    """
    Get character descriptions from the given URL
    """
    page = requests.get(url)
    valid, edit_page = check_snapshot_date(page, url)
    if not valid:
        page = edit_page
    soup = BeautifulSoup(page.content, "html.parser")
    data = []

    current_attempt = 1

    while current_attempt <= max_attempts:
        major_char_heading = soup.find("p", class_="litNoteTextHeading", text="Major Characters")
        if major_char_heading:
            characters = major_char_heading.find_next_siblings("p", class_="litNoteText")
            for c in characters:
                char_name = c.findNext("strong").text.strip()
                descr = re.sub(char_name, "", c.text).strip()
                data.append({"id": book_id, "book": title, "author": author, "character": char_name,
                             "description": descr, "source": "Cliffnotes", "url": url})
            break

        paragraphs = soup.find_all("p", class_="litNoteText")
        if paragraphs:
            for p in paragraphs:
                if p.findChildren("strong"):
                    char_name = p.findNext("strong").text.strip()
                    descr = re.sub(char_name, "", p.text).strip()

                elif p.findNext("b"):
                    char_name = p.findNext("b").text.strip()
                    descr = re.sub(char_name, "", p.text, count=1).strip()
                else:
                    continue

                data.append({"id": book_id, "book": title, "author": author, "character": char_name,
                             "description": descr, "source": "Cliffnotes", "url": url})
            break
        headings = soup.find_all("p", class_="litNoteTextHeading")

        if headings:
            for h in headings:
                char_name = h.text.strip()
                descr = h.findNext("p").text.strip()
                data.append({"id": book_id, "book": title, "author": author, "character": char_name,
                             "description": descr, "source": "Cliffnotes", "url": url})
            break

        current_attempt += 1
        time.sleep(30)

    if current_attempt >= max_attempts:
        return None
        # print("Failed to get character description for {}".format(title))

    return data


def extract_char_analysis_urls(url):
    """Extract character analysis URLs from the given character list URL."""

    phrase = "character-list"
    page = requests.get(urljoin(url[:url.rfind('/') + 1], phrase))
    soup = BeautifulSoup(page.content, "html.parser")

    character_analysis_urls = []

    list_items = soup.find_all("li")
    for item in list_items:
        url_suffix = item.findNext("a")["href"]

        if "character-analysis" in url_suffix.split("/"):
            base_url = urlsplit(url).netloc
            full_url = "https://" + base_url + url_suffix

            if full_url not in character_analysis_urls:
                character_analysis_urls.append(full_url)

    return character_analysis_urls


def get_character_analysis(book_id, title, author, url):
    """Get character analysis from the given URL."""

    data = []
    page = requests.get(url)
    valid, edit_page = check_snapshot_date(page, url)
    if not valid:
        page = edit_page

    analysis_soup = BeautifulSoup(page.content, "html.parser")

    article = analysis_soup.find("article")
    if article:
        full_title = article.find("h2").text.strip()
        character_name = full_title.split("Character Analysis")[1].strip()
        analysis_text = ""
        paragraphs = article.find_all("p", class_="litNoteText")
        for p in paragraphs:
            analysis_text += p.text.strip() + "\n\n"

        data.append(
            {"id": book_id, "book": title, "author": author, "character": character_name,
             "analysis": analysis_text, "source": "Cliffnotes", "url": url})

    return data


if __name__ == "__main__":
    output = get_data(2833, "The Portrait of a Lady", "Henry James",
                      "https://web.archive.org/web/20230616062923/https://www.cliffsnotes.com/literature/p/the"
                      "-portrait-of-a-lady/book-summary",
                      "analysis")

    print(output)
