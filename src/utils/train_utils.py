from unsloth import FastLanguageModel


def load_unsloth_model(checkpoint_path, max_input_length, inference=True):
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=checkpoint_path,
        max_seq_length=max_input_length,
        dtype=None,
        load_in_4bit=False,
    )
    if inference:
        FastLanguageModel.for_inference(model)

    return model, tokenizer


def print_trainable_parameters(model):
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}")
