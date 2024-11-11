import argparse
import json
import os
import re
import time

import pandas as pd

from websites import litcharts, sparknotes, cliffsnotes, shmoop, gradesaver


def get_data_from_website(book_id, title, author, website, url, data_type, max_attempts=3, exp_base=3):
    current_attempt = 0
    while current_attempt <= max_attempts:
        try:
            scraper_func = {
                'litcharts': litcharts.get_data,
                'sparknotes': sparknotes.get_data,
                'cliffsnotes': cliffsnotes.get_data,
                'shmoop': shmoop.get_data,
                'gradesaver': gradesaver.get_data,
            }.get(website)
            return scraper_func(book_id, title, author, url, data_type)

        except Exception as e:
            current_attempt += 1
            time.sleep(exp_base ** current_attempt)

            continue

    return None


def create_data(data_file, save_path, data_type="description", max_attempts=3, exp_base=3):
    """
    Scrape and create a dataset from literary websites.
    """

    if data_type not in ["description", "analysis"]:
        raise ValueError("data_type must be either 'description' or 'analysis'")

    dtype_dict = {
        'BookId': 'int64',
        'Title': 'string',
        'Author': 'string',
        'Url': 'string'
    }

    data = pd.read_csv(data_file, sep="\t", dtype=dtype_dict, index_col=False)

    if not os.path.exists(os.path.join(save_path, data_type)):
        os.makedirs(os.path.join(save_path, data_type))

    f_data = open(os.path.join(save_path, f"{data_type}/{data_type}_data.jsonl"), "a")
    f_written = open(os.path.join(save_path, f"{data_type}_written.tsv"), "a+")

    if not os.stat(os.path.join(save_path, f"{data_type}_written.tsv")).st_size:
        f_written.write("\t".join(["BookId", "Title", "Author", "Url"]) + "\n")
    else:
        data_written = pd.read_csv(os.path.join(save_path, f"{data_type}_written.tsv"), sep="\t", dtype=dtype_dict)

        data = pd.concat([data, data_written])
        data = data.drop_duplicates(keep=False)

    failed_data = []
    for i, row in data.iterrows():

        website = re.search(r"www\.(\w+)\.com", row["Url"]).group(1)

        print(f"{i} Scraping data from: ", row["Url"], row["Title"])

        scraped_data = get_data_from_website(row["BookId"], row["Title"], row["Author"], website, row["Url"],
                                             data_type, max_attempts, exp_base)

        if scraped_data is not None:
            for data_row in scraped_data:
                f_data.write(json.dumps(data_row) + "\n")
                f_data.flush()
            f_written.write('\t'.join(map(str, row)) + '\n')
            f_written.flush()
        else:
            print("Fail to scrape data from: ", row["Url"], row["Title"])
            failed_data.append(row)

    f_data.close()
    f_written.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Scrape literary data from websites.")
    parser.add_argument("--data_file", help="Path to the input TSV file containing book data.")
    parser.add_argument("--save_path", help="Directory where scraped data will be saved.")
    parser.add_argument("--data_type", choices=["description", "analysis"], default="description",
                        help="Type of data to scrape.")
    parser.add_argument("--max_attempts", type=int, default=3, help="Maximum number of attempts for scraping.")
    parser.add_argument("--exp_base", type=int, default=3, help="Base for exponential backoff.")
    args = parser.parse_args()

    create_data(
        args.data_file,
        args.save_path,
        data_type=args.data_type,
        max_attempts=args.max_attempts,
        exp_base=args.exp_base
    )
