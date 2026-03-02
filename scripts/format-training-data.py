"""
Format training data for QLoRA fine-tuning with Unsloth.

Usage:
    python scripts/format-training-data.py --input training_examples.jsonl --output formatted_dataset.jsonl
"""

import argparse
import json

def format_data(input_path: str, output_path: str):
    valid = 0
    invalid = 0

    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        for line in fin:
            try:
                example = json.loads(line.strip())
                messages = example.get("messages", [])

                # Validate structure
                if len(messages) < 3:
                    invalid += 1
                    continue

                roles = [m["role"] for m in messages]
                if roles[0] != "system" or roles[1] != "user" or "assistant" not in roles:
                    invalid += 1
                    continue

                # Ensure all messages have content
                if not all(m.get("content") or m.get("tool_calls") for m in messages):
                    invalid += 1
                    continue

                # Write validated example (just the messages, strip metadata)
                fout.write(json.dumps({"messages": messages}) + "
")
                valid += 1

            except (json.JSONDecodeError, KeyError):
                invalid += 1

    print(f"Valid: {valid}, Invalid: {invalid}, Total: {valid + invalid}")
    print(f"Output: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    format_data(args.input, args.output)

