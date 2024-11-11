import json


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
