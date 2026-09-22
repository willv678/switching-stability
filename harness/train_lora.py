import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)

MODEL_ID = "Qwen/Qwen2.5-Coder-3B-Instruct"
TRAIN_FILE = "sft_train.jsonl"
VAL_FILE = "sft_val.jsonl"
OUTPUT_DIR = "./autolab_lora_adapter"

def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype=torch.bfloat16,
        device_map="auto"
    )

    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    dataset = load_dataset("json", data_files={"train": TRAIN_FILE, "validation": VAL_FILE})

    def tokenize_batch(batch):
        texts = [
            tokenizer.apply_chat_template(msg, tokenize=False, add_generation_prompt=False)
            for msg in batch["messages"]
        ]
        tokens = tokenizer(texts, max_length=512, truncation=True)
        tokens["labels"] = [list(ids) for ids in tokens["input_ids"]]
        return tokens

    tokenized_train = dataset["train"].map(
        tokenize_batch,
        batched=True,
        remove_columns=dataset["train"].column_names
    )
    tokenized_val = dataset["validation"].map(
        tokenize_batch,
        batched=True,
        remove_columns=dataset["validation"].column_names
    )

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        eval_accumulation_steps=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        num_train_epochs=3,
        logging_steps=5,
        save_strategy="epoch",
        eval_strategy="epoch",
        bf16=True,
        gradient_checkpointing=True,
        remove_unused_columns=False
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        pad_to_multiple_of=8,
        return_tensors="pt",
        padding=True
    )

    trainer = Trainer(
        model=model,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=data_collator,
        args=training_args
    )

    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"[*] LoRA adapter saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()