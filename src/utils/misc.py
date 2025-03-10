import json
import os
import re
from datetime import datetime

import requests
import yaml
from dateutil.relativedelta import relativedelta  # Install via pip if needed


def read_jsonl(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            data.append(json.loads(line))

    return data


def write_jsonl(data, file_path):
    with open(file_path, 'w') as f:
        for row in data:
            f.write(json.dumps(row) + '\n')


def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    return config


def save_config(data, path):
    with open(path, "w") as file:
        yaml.safe_dump(data, file)


def truncate_text(text, tokenizer, max_length=4096):
    paragraphs = text.split("\n\n")
    truncated_paragraphs = []
    current_length = 0

    for p in paragraphs:
        if (len(tokenizer.encode(p)) + current_length) > max_length:
            break
        else:
            truncated_paragraphs.append(p)
            current_length += len(tokenizer.encode(p))

    return "\n\n".join(truncated_paragraphs)


def segment_text(text, tokenizer, max_length=4096):
    paragraphs = text.split("\n\n")
    segments = []
    segment_paragraphs = []
    current_length = 0
    for p in paragraphs:
        token_length = len(tokenizer.encode(p))
        if (token_length + current_length) > max_length:
            segments.append("\n\n".join(segment_paragraphs))
            current_length = token_length
            segment_paragraphs = [p]
        else:
            segment_paragraphs.append(p)
            current_length += token_length

    if segment_paragraphs:
        segments.append("\n\n".join(segment_paragraphs))

    return segments


def load_prompt(file_path):
    with open(file_path, 'r') as file:
        prompt_template = file.read()
    return prompt_template


def format_prompt(prompt_template, **kwargs):
    return prompt_template.format(**kwargs)


def get_new_experiment_path(base_path, prefix="eval_"):
    entries = os.listdir(base_path)
    pattern = re.compile(r'^' + re.escape(prefix) + r'(\d+)$')

    max_id = -1
    for entry in entries:
        match = pattern.match(entry)
        if match:
            exp_id = int(match.group(1))
            if exp_id > max_id:
                max_id = exp_id

    new_id = 0 if max_id == -1 else max_id + 1

    new_path = os.path.join(base_path, f"{prefix}{new_id}")
    os.makedirs(new_path)

    return new_path


def load_template(method, task="description"):
    if method == "truncate":
        if task == "description":
            return load_prompt("../../prompts/description_prompt.txt")
        elif task == "analysis":
            return load_prompt("../../prompts/analysis_prompt.txt")
    elif method == "hierarchical":
        if task == "description":
            general_prompt_template = load_prompt("../../prompts/description_prompt.txt")
            merge_prompt_template = load_prompt("../../prompts/merge_prompt_description.txt")
            return general_prompt_template, merge_prompt_template
        elif task == "analysis":
            general_prompt_template = load_prompt("../../prompts/analysis_prompt.txt")
            merge_prompt_template = load_prompt("../../prompts/merge_prompt_analysis.txt")
            return general_prompt_template, merge_prompt_template
    else:
        raise ValueError("Invalid method given.")


def check_snapshot_date(page, url, max_date=20241112000000):
    """
    Check if the snapshot of the scraped page is before the max_date (in case of new created snapshot which is sooner
    than the originally used date). If not, find the closest previous snapshot.
    """

    max_date = datetime.strptime(str(max_date), "%Y%m%d%H%M%S")

    final_url = page.url
    parts = final_url.split("/")
    current_timestamp_str = parts[4].replace("id_", "")

    url_parts = url.split("/")
    if len(url_parts) <= 4:
        return True, page

    initial_timestamp_str = url_parts[4].replace("id_", "")

    try:
        initial_date = datetime.strptime(initial_timestamp_str, "%Y%m%d%H%M%S")
    except ValueError:
        initial_date = datetime.strptime(initial_timestamp_str, "%Y")

    actual_date = datetime.strptime(current_timestamp_str, "%Y%m%d%H%M%S")

    valid = True
    count = 1
    response = page

    while actual_date >= max_date:
        adjusted_date = initial_date - relativedelta(years=count)
        new_timestamp = adjusted_date.strftime("%Y%m%d%H%M%S")
        adjusted_url = url.replace(initial_timestamp_str, new_timestamp)

        response = requests.get(adjusted_url)
        final_url = response.url
        parts = final_url.split("/")

        current_timestamp_str = parts[4].replace("id_", "")
        actual_date = datetime.strptime(current_timestamp_str, "%Y%m%d%H%M%S")
        valid = False
        count += 1
        if count >= 5:
            break

    return valid, response
