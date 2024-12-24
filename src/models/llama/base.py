from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


def load_model(model_name):
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto",
                                                 use_auth_token=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True)
    return model, tokenizer


def prompt_model(prompt, tokenizer, model, generation_params):
    messages = [{"role": "user", "content": prompt}]

    terminators = [
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(input_ids, eos_token_id=terminators, **generation_params)
    output = tokenizer.decode(outputs[:, input_ids.shape[-1]:].squeeze(), skip_special_tokens=True)

    return output


if __name__ == "__main__":

    model_name = "meta-llama/Meta-Llama-3-8B-Instruct"

    load_model(model_name)
