import re
import urllib.parse

import requests
from bs4 import BeautifulSoup


def scrape():
    """
    Scrape url links of SparkNotes website
    """

    base_url = "https://www.sparknotes.com/"
    all_studies = urllib.parse.urljoin(base_url, "lit/")

    page = requests.get(all_studies)
    soup = BeautifulSoup(page.content, "html.parser")

    study_link_class = (
        "hub-AZ-list__card__title__link "
        "hub-AZ-list__card__title__link--full-card-link no-link"
    )

    lit_studies = soup.find_all("a", class_=study_link_class)
    lit_titles = []
    lit_authors = []
    lit_websites = []

    for link in lit_studies:
        lit_titles.append(link.text)
        if link.find_parent().find_next_sibling():
            lit_authors.append(link.find_parent().find_next_sibling().text)
        else:
            lit_authors.append("N/A")
        lit_websites.append(urllib.parse.urljoin(base_url, link["href"]))

    return lit_titles, lit_authors, lit_websites


def get_data(book_id, title, author, base_url, data_type):
    """
    Scrape characters description, analysis or book summary base on data_type
    """

    if data_type == "description":
        url = urllib.parse.urljoin(base_url, "characters")
        return get_character_description(book_id, title, author, url)
    elif data_type == "analysis":
        url = urllib.parse.urljoin(base_url, "characters")

        char_urls = extract_char_analysis_urls(url, base_url)
        char_analysis = []
        for char_url in char_urls:
            char_analysis.extend(get_character_analysis(book_id, title, author, char_url))
        return char_analysis
    elif data_type == "summary":
        summary_url = urllib.parse.urljoin(base_url, "summary")
        return get_summary(summary_url)


def get_character_description(book_id, title, author, url):
    """
    Scrape character descriptions for a given url
    """

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    data = []

    # try:
    main_content = soup.find("div", class_="mainTextContent main-container")

    if main_content:
        header_tags = main_content.find_all("h3")

        for header in header_tags:
            char_name = header.text
            siblings = header.findNextSiblings("p")
            descr = siblings[0].text
            descr = ' '.join(i.strip() for i in descr.split('\n'))
            data.append(
                {"id": book_id, "book": title, "author": author, "character": char_name,
                 "description": descr.strip(), "source": "SparkNotes", "url": url})
    else:
        list_items = soup.find("ul", class_="mainTextContent__list-content").find_all("li", recursive=True)
        for item in list_items:
            char_name = item.find("h3").text
            descr = item.find("p").text
            descr = re.sub("\n", "", descr)
            data.append(
                {"id": book_id, "book": title, "author": author, "character": char_name,
                 "description": descr.strip(), "source": "SparkNotes", "url": url})
    # except Exception as e:
    #     print(f"Error parsing character descriptions: {e}")
    #     return None

    return data


def extract_char_analysis_urls(url, base_url):
    """
    Extract character analysis URLs from the characters page.
    """

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    character_analysis_urls = []

    nodes = soup.find_all("a", recursive=True)
    for n in nodes:
        if "in-depth" in n.text:
            _char_name = n["href"].rstrip('/').split('/')[-1]

            character_url = urllib.parse.urljoin(base_url + "character/", _char_name)

            if character_url not in character_analysis_urls:
                character_analysis_urls.append(character_url)

    return character_analysis_urls


def get_character_analysis(book_id, title, author, url):
    """
    Scrape character analysis from a given url
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    data = []

    char_name_tag = soup.find("span", class_="interior-sticky-nav__title__section", recursive=True)
    if char_name_tag:
        char_name = soup.find("span", class_="interior-sticky-nav__title__section", recursive=True).text.strip()
        analysis = ""
        main_content = soup.find("div", class_="mainTextContent main-container")

        if main_content:
            for element in main_content:
                analysis += re.sub("\s+", " ", element.text).strip() + "\n"
            data.append(
                {"id": book_id, "book": title, "author": author, "character": char_name,
                 "analysis": analysis.strip(), "source": "SparkNotes", "url": url})

        else:
            content_txt = soup.find("div", class_="content_txt")
            if content_txt:
                paragraphs = content_txt.find_all("p")
                for p in paragraphs:
                    analysis += p.text.strip()

            data.append(
                {"id": book_id, "book": title, "author": author, "character": char_name,
                 "analysis": analysis.strip(), "source": "SparkNotes", "url": url})

    return data


def get_summary(url):
    """
    Scrape the summary from a given URL
    """

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    if soup.find("div", class_="mainTextContent main-container"):
        main_content = soup.find("div", class_="mainTextContent main-container")
    else:
        main_content = soup.find("div", class_="studyGuideText hack-to-hide-first-h2")

    if not main_content:
        return None

    summary = ""
    for element in main_content:
        summary += re.sub("\s+", " ", element.text).strip() + "\n"

    return summary.lstrip()


if __name__ == "__main__":

    output = get_data(98, "A Tale of Two Cities", "Charles Dickens",
                      "https://web.archive.org/web/20221109035530/https://www.sparknotes.com/lit/a-tale-of-two-cities/",
                      "analysis")
    print(output)
