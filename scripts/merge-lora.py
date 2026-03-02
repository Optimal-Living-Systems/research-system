"""
Merge LoRA adapter weights with base model for deployment.

Usage:
    pip install transformers peft accelerate
    python scripts/merge-lora.py --base-model Qwen/Qwen2.5-14B-Instruct --lora-path ./lora-adapter --output ./merged-model
"""

import argparse

def merge(base_model: str, lora_path: str, output: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print(f"Loading base model: {base_model}")
    model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype="auto", device_map="auto")
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    print(f"Loading LoRA adapter: {lora_path}")
    model = PeftModel.from_pretrained(model, lora_path)

    print("Merging weights...")
    model = model.merge_and_unload()

    print(f"Saving merged model to: {output}")
    model.save_pretrained(output)
    tokenizer.save_pretrained(output)
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--lora-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    merge(args.base_model, args.lora_path, args.output)

