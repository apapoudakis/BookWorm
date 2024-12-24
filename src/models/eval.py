import argparse
import json
import os

from src.utils.train_utils import load_unsloth_model
from src.models.llama import base
from src.utils.misc import (read_jsonl, truncate_text, segment_text, format_prompt, load_config, save_config,
                            get_new_experiment_path, load_template)


def main(config):
    data_config, eval_config, generate_config = config["data_params"], config["eval_params"], config["generate_params"]

    supported_models = {
        "llama": base,
    }

    for model in supported_models:
        if model in eval_config["model_name"].lower():
            model_func = supported_models[model]

    # load base or fine-tuned checkpoint
    if eval_config["checkpoint_path"] is not None:
        model, tokenizer = load_unsloth_model(eval_config["checkpoint_path"], eval_config["truncate_length"],
                                              inference=True)
    else:

        model, tokenizer = model_func.load_model(eval_config["model_name"])

    prompt_template = load_template(eval_config["method"], task="description")

    data = read_jsonl(os.path.join(data_config["data_path"], eval_config["split"] + ".jsonl"))

    predictions = []

    experiment_path = get_new_experiment_path(eval_config["save_path"])
    f = open(os.path.join(experiment_path, "preds.jsonl"), "a")
    save_config(config, os.path.join(experiment_path, "config.yaml"))

    for i, sample in enumerate(data):
        print(i)

        if eval_config["method"] == "truncate":

            truncated_context = truncate_text(sample["input"], tokenizer, max_length=eval_config["truncate_length"])

            variables = {
                "character": sample["character"],
                "context": truncated_context
            }

            prompt = format_prompt(prompt_template, **variables)

            output = model_func.prompt_model(prompt, tokenizer, model, generate_config)
            print(output)
            pred_data = {"book": sample["book"], "character": sample["character"], "output": output}

        elif eval_config["method"] == "hierarchical":
            general_prompt_template, merge_prompt_template = prompt_template
            segments = segment_text(sample["input"], tokenizer, max_length=eval_config["truncate_length"])

            outputs = []
            for segment in segments:
                variables = {
                    "character": sample["character"],
                    "context": segment
                }
                prompt = format_prompt(general_prompt_template, **variables)
                output = model_func.prompt_model(prompt, tokenizer, model, generate_config)
                outputs.append(output)

            intermediate_descriptions = "\n\n".join(outputs)

            variables = {
                "character": sample["character"],
                "descriptions": intermediate_descriptions
            }

            prompt = format_prompt(merge_prompt_template, **variables)
            final_output = model_func.prompt_model(prompt, tokenizer, model, generate_config)
            print(final_output)
            pred_data = {"book": sample["book"], "character": sample["character"], "segmet_outputs": outputs,
                         "output": final_output}
        else:
            raise ValueError("Method not supported")

        predictions.append(pred_data)

        f.write(json.dumps(pred_data) + "\n")
        f.flush()

    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-d', type=str, required=True, help='Path to the configuration file.')
    args = parser.parse_args()

    yaml_config = load_config(args.config)

    main(yaml_config)
