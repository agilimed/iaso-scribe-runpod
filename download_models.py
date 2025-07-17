#!/usr/bin/env python3
"""
Pre-download models during Docker build to avoid runtime downloads
"""
import os
import urllib.request
import sys

def download_with_progress(url, destination):
    """Download file with progress bar"""
    def download_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100.0 / total_size, 100)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\rDownloading: {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent:.1f}%)")
        sys.stdout.flush()
    
    print(f"Downloading to {destination}")
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    urllib.request.urlretrieve(url, destination, reporthook=download_progress)
    print("\nDownload complete!")

def main():
    # Download Whisper model
    print("Downloading Whisper medium model...")
    from faster_whisper import WhisperModel
    WhisperModel("medium", device="cpu", compute_type="int8", download_root="/models/whisper")
    print("Whisper model downloaded!")
    
    # Download Phi-4 model
    phi_url = "https://huggingface.co/bartowski/microsoft_Phi-4-reasoning-plus-GGUF/resolve/main/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf"
    phi_path = "/models/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf"
    
    if not os.path.exists(phi_path):
        print(f"\nDownloading Phi-4 model (11.44 GB)...")
        download_with_progress(phi_url, phi_path)
    else:
        print(f"Phi-4 model already exists at {phi_path}")

if __name__ == "__main__":
    main()