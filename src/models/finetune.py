import argparse
import os

import datasets
import pandas as pd
import wandb
from tqdm.auto import tqdm
from transformers import AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel, is_bfloat16_supported

from src.utils.misc import load_config, truncate_text, format_prompt
from src.utils.train_utils import load_unsloth_model

tqdm.pandas()


def tokenize_example(train_config, tokenizer, text):
    prompt, description = text

    messages = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": description}
    ]

    full_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    tokenized_full_prompt = tokenizer(
        full_prompt,
        truncation=True,
        max_length=train_config["max_input_length"],
        padding=False,
        return_tensors=None
    )

    input_ids = tokenized_full_prompt["input_ids"]

    assistant_message = tokenizer.apply_chat_template(
        [{"role": "assistant", "content": description}],
        tokenize=False,
        add_generation_prompt=True
    )

    tokenized_assistant = tokenizer(
        assistant_message,
        truncation=True,
        max_length=train_config["max_input_length"],
        padding=False,
        return_tensors=None
    )
    assistant_ids = tokenized_assistant["input_ids"]

    # Create labels, masking the non-assistant tokens with -100
    labels = [-100] * (len(input_ids) - len(assistant_ids)) + assistant_ids
    tokenized_full_prompt["labels"] = labels

    # code to test the masking
    # print(tokenizer.decode(trainer.train_dataset[0]["input_ids"]))
    # space = tokenizer(" ", add_special_tokens = False).input_ids[0]
    # print("\n---------------------------------------------------\n")
    # print(tokenizer.decode([space if x == -100 else x for x in trainer.train_dataset[0]["labels"]]))

    return tokenized_full_prompt


def generate_and_tokenize_prompt(train_config, tokenizer, data_point, prompt_template):
    return tokenize_example(train_config, tokenizer,
                            formatting_func(data_point, train_config, tokenizer, prompt_template))


def formatting_func(example, train_config, tokenizer, prompt_template):
    variables = {
        "character": example["character"],
        "context": example["input"]
    }

    input_text = format_prompt(prompt_template, **variables)

    truncated_text = truncate_text(input_text, tokenizer, max_length=train_config["truncate_length"])

    return truncated_text, example["description"]


def prepare_data(tokenizer, data_config, train_config):
    train_df = pd.read_json(os.path.join(data_config['data_path'], "train.jsonl"), lines=True)
    val_df = pd.read_json(os.path.join(data_config['data_path'], "val.jsonl"), lines=True)

    prompt_template = open(data_config['prompt_path']).read()

    train_dataset = datasets.Dataset.from_pandas(train_df)
    val_dataset = datasets.Dataset.from_pandas(val_df)

    tokenized_train_dataset = train_dataset.map(
        lambda x: generate_and_tokenize_prompt(train_config, tokenizer, x, prompt_template))
    tokenized_val_dataset = val_dataset.map(
        lambda x: generate_and_tokenize_prompt(train_config, tokenizer, x, prompt_template))

    return tokenized_train_dataset, tokenized_val_dataset


def main(config):
    data_config, train_config, experiment_config, lora_config = config["data_params"], config["train_params"], config[
        "experiment_params"], config["lora_params"]

    model, _ = load_unsloth_model(train_config["model_name"], train_config["max_input_length"])

    tokenizer = AutoTokenizer.from_pretrained(
        train_config["model_name"],
        model_max_length=train_config["max_input_length"],
        padding_side="right",
        add_eos_token=True,
    )

    tokenizer.pad_token = tokenizer.eos_token
    model.config.pad_token_id = tokenizer.pad_token_id

    if train_config["apply_lora"]:
        model = FastLanguageModel.get_peft_model(
            model,
            r=lora_config["r"],  # 8, 16, 32, 64, 128
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj", ],
            lora_alpha=lora_config["lora_alpha"],
            lora_dropout=lora_config["lora_dropout"],  # Supports any, but = 0 is optimized
            bias="none",  # Supports any, but = "none" is optimized
            use_gradient_checkpointing="unsloth",  # True or "unsloth" for very long context
            random_state=train_config["seed"],
            use_rslora=False,  # We support rank stabilized LoRA
            loftq_config=None,  # And LoftQ
        )

    tokenized_train_data, tokenized_val_data = prepare_data(tokenizer, data_config, train_config)

    experiment_path = os.path.join(experiment_config['save_experiment'], experiment_config['model'],
                                   experiment_config['experiment_name'], f"seed_{train_config['seed']}")

    wandb.init(
        project=experiment_config["wandb_project"],
        name=experiment_config["model"] + "-" + experiment_config["experiment_name"]
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=tokenized_train_data,
        eval_dataset=tokenized_val_data,
        max_seq_length=train_config["max_input_length"],
        dataset_num_proc=2,
        packing=True,
        args=TrainingArguments(
            per_device_train_batch_size=train_config["batch_size"],
            per_device_eval_batch_size=train_config["batch_size"],
            gradient_accumulation_steps=train_config["gradient_accumulation_steps"],
            evaluation_strategy="steps",
            max_steps=train_config["max_steps"],
            warmup_steps=train_config["warm_up_steps"],
            learning_rate=train_config["lr"],
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=train_config["logging_steps"],
            optim="adamw_8bit",
            weight_decay=train_config["weight_decay"],
            lr_scheduler_type="linear",
            seed=train_config["seed"],
            output_dir=experiment_path,
            do_eval=True,
            report_to="wandb",
            save_strategy=train_config["save_strategy"],
        ),
    )

    trainer.train()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-d', type=str, required=True, help='Path to the data configuration file.')
    args = parser.parse_args()

    yaml_config = load_config(args.config)

    main(yaml_config)
