from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "models" / "Qwen2.5-3B-Instruct"


# --------------------------------------------------
# Check model
# --------------------------------------------------

print("=" * 60)
print("LOCAL QWEN MODEL TEST")
print("=" * 60)

print(f"Model path: {MODEL_PATH}")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found at: {MODEL_PATH}"
    )


# --------------------------------------------------
# Load tokenizer
# --------------------------------------------------

print("\n[1/3] Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH
)

print("Tokenizer loaded.")


# --------------------------------------------------
# Load model
# --------------------------------------------------

print("\n[2/3] Loading Qwen model...")
print("This can take some time.")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype="auto",
)

print("Model loaded successfully.")

print(f"Model device: {model.device}")


# --------------------------------------------------
# Test query
# --------------------------------------------------

messages = [
    {
        "role": "system",
        "content": (
            "You are a telecom network troubleshooting assistant. "
            "Answer clearly and concisely."
        ),
    },
    {
        "role": "user",
        "content": (
            "What could cause poor network performance "
            "during winter in Chennai?"
        ),
    },
]


print("\n[3/3] Generating response...")

inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
)

inputs = inputs.to(model.device)


with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.2,
        do_sample=True,
    )


# --------------------------------------------------
# Decode only generated answer
# --------------------------------------------------

generated_tokens = outputs[
    0,
    inputs["input_ids"].shape[-1]:
]

answer = tokenizer.decode(
    generated_tokens,
    skip_special_tokens=True,
)


print("\n" + "=" * 60)
print("LOCAL QWEN RESPONSE")
print("=" * 60)

print(answer)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)