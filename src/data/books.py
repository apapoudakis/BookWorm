import argparse
import os

import pandas as pd
from gutenbergpy import textget


def get_books(data_file, save_path):
    data = pd.read_csv(data_file, sep="\t")

    for i, row in data.iterrows():
        raw_book = textget.get_text_by_id(row["Id"])
        clean_book = textget.strip_headers(raw_book)

        if not os.path.exists(os.path.join(save_path, str(row["Id"]))):
            os.makedirs(os.path.join(save_path, str(row["Id"])))

        with open(os.path.join(save_path, str(row["Id"]), "book.txt"), 'wb') as raw_file:
            raw_file.write(raw_book)

        with open(os.path.join(save_path, str(row["Id"]), "book_cleaned.txt"), 'wb') as clean_file:
            clean_file.write(clean_book)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Download Gutenberg Books")
    parser.add_argument("--data_file", help="Path to the input TSV file containing book data.")
    parser.add_argument("--save_path", help="Directory where downloaded books will be saved.")
    args = parser.parse_args()

    get_books(
        args.data_file,
        args.save_path,
    )
