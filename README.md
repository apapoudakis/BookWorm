# BookWorm

This repository contains the code for our paper, BookWorm: A Dataset for Character Description and Analysis 
(EMNLP Findings 2024) [[Paper]](https://arxiv.org/abs/2410.10372)

We are not allowed to share the scraped data but you can reproduce the dataset using our code scripts with the webarchived urls. 

For any question please email me: [a.papoudakis@sms.ed.ac.uk](a.papoudakis@sms.ed.ac.uk)

### Python Environment
```
conda create -n bookworm_env python=3.10
conda activate bookworm_env
pip install -r requirements.txt
```

### Scrape Description and Analysis Data
To scrape character descriptions and analyses data from the different websites, use the command below. If some of the archived links fail to download, simply rerun the command, it will automatically attempt to download any previously failed links.

```
python collect_data.py --data_file ../../data/description_data.tsv --save_path ../../data/corpus/ --data_type description --max_attempts 3 --exp_base 3 
```

### Download Gutenberg Books

```
python books.py --data_file ../../data/books.tsv --save_path ../../data/corpus/books
```

### Preprocess
To filter out short descriptions and analyses as described in our work, please run the following command.

```
python prepare_data.py --action filter --dataset_path ../../data/corpus/description/description_data.jsonl --tokens_threshold 30 --output_path ../../data/corpus/description --task description
```

To split the dataset into train/val/test splits use the following command:

```
python prepare_data.py --action split --dataset_path ../../data/corpus/description/description_data-filtered-30.jsonl --split_path ../../data/splits/description --save_path ../../data/corpus/description
```

### Experiments

You can run the experiments of our paper and finetune a model by specifying the configuration file train.yaml and run the following command:

```
python finetune.py --config ../../config/train.yaml
```

You can run zero-shot or finetuned models using the following command:

```
python eval.py --config ../../config/eval.yaml
```

### Citation

```
@inproceedings{papoudakis2024bookworm,
  title={BookWorm: A Dataset for Character Description and Analysis},
  author={Papoudakis, Argyrios and Lapata, Mirella and Keller, Frank},
  booktitle={Findings of the Association for Computational Linguistics: EMNLP 2024},
  pages={4471--4500},
  year={2024}
}
