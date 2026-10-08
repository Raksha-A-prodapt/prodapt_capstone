from huggingface_hub import snapshot_download


print("Downloading Qwen2.5-3B-Instruct...")
print("This may take several minutes because the model is about 6 GB.")


model_path = snapshot_download(
    repo_id="Qwen/Qwen2.5-3B-Instruct",
    local_dir="models/Qwen2.5-3B-Instruct",
)


print("\n========================================")
print("DOWNLOAD COMPLETE")
print("========================================")
print(f"Model location: {model_path}")