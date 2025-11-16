#!/usr/bin/env python3
"""Test Whisper GPU acceleration"""
import whisper
import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")

if torch.cuda.is_available():
    print(f"\nGPU Device: {torch.cuda.get_device_name(0)}")
    device_cap = torch.cuda.get_device_capability(0)
    print(f"Compute Capability: {device_cap[0]}.{device_cap[1]}")

print("\nLoading Whisper base model on GPU...")
model = whisper.load_model("base", device="cuda")

# Check where model parameters are
device = next(model.parameters()).device
print(f"✓ Whisper model loaded on: {device}")

print("\nWhisper is ready to use GPU acceleration!")
