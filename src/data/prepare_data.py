import argparse
import os
from pathlib import Path

import pandas as pd
from nltk.tokenize import word_tokenize


def filter_corpus(dataset_path, tokens_threshold, output_path, task="description"):
    data = pd.read_json(dataset_path, lines=True)

    data = data[data[task].apply(lambda x: len(word_tokenize(x)) > tokens_threshold)]
    data_name = Path(dataset_path).stem
    data.to_json(os.path.join(output_path, data_name + f"-filtered-{tokens_threshold}.jsonl"),
                 orient='records', lines=True)


def split_corpus(dataset_path, split_path, save_path):
    train = pd.read_csv(os.path.join(split_path, "train.tsv"), sep="\t")
    val = pd.read_csv(os.path.join(split_path, "val.tsv"), sep="\t")
    test = pd.read_csv(os.path.join(split_path, "test.tsv"), sep="\t")
    full_corpus = pd.read_json(dataset_path, lines=True)

    train_split = full_corpus[full_corpus["id"].isin(train["BookId"].unique())]
    train_split.to_json(os.path.join(save_path, "train.jsonl"), orient='records', lines=True)

    val_split = full_corpus[full_corpus["id"].isin(val["BookId"].unique())]
    val_split.to_json(os.path.join(save_path, "val.jsonl"), orient='records', lines=True)

    test_split = full_corpus[full_corpus["id"].isin(test["BookId"].unique())]
    test_split.to_json(os.path.join(save_path, "test.jsonl"), orient='records', lines=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Script for filtering or splitting corpus data.")
    parser.add_argument('--action', type=str, choices=['filter', 'split'], required=True,
                        help="Action to perform: 'filter' or 'split'.")

    parser.add_argument('--dataset_path', type=str, required=True, help='Path to the dataset')
    parser.add_argument('--task', type=str, default='description', help='Task name')
    parser.add_argument('--tokens_threshold', type=int, help='Tokens threshold for filtering')
    parser.add_argument('--output_path', type=str, help='Output path for filtered data')
    parser.add_argument('--split_path', type=str, help='Path to the split files')
    parser.add_argument('--save_path', type=str, help='Path to save the splits')

    args = parser.parse_args()

    if args.action == 'filter':
        if args.tokens_threshold is None or args.output_path is None:
            parser.error("--tokens_threshold and --output_path are required for action 'filter'.")
        filter_corpus(args.dataset_path, args.tokens_threshold, args.output_path, args.task)
    elif args.action == 'split':
        if args.split_path is None or args.save_path is None:
            parser.error("--split_path and --save_path are required for action 'split'.")
        split_corpus(args.dataset_path, args.split_path, args.save_path)
