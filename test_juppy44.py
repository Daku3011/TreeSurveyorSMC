"""
Test CLI script for juppy44/plant-identification-2m-vit-b
Run: python test_juppy44.py [optional_path_to_image]
"""
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

from services.vit_classifier import get_vit_pipeline, classify_species_vit, analyze_with_juppy44, get_hf_token

def main():
    print("=" * 60)
    print("🌿 Testing juppy44/plant-identification-2m-vit-b")
    print("=" * 60)
    
    token = get_hf_token()
    if token:
        masked = token[:6] + "..." + token[-4:] if len(token) > 10 else "***"
        print(f"🔑 Hugging Face Token Detected: {masked}")
    else:
        print("⚠️ No HF_TOKEN detected in .env or ~/.cache/huggingface/token.")
        
    print("\n[1/2] Checking model weights & gated access...")
    processor, model, err = get_vit_pipeline()
    if err:
        print(f"\n❌ Model Access Notice:\n{err}")
        print("\n👉 To enable this model:")
        print("1. Visit https://huggingface.co/juppy44/plant-identification-2m-vit-b")
        print("2. Log in with your Hugging Face account (e.g. Dwarkesh3011)")
        print("3. Click 'Acknowledge / Request Access' (terms are auto-accepted)")
        print("4. Re-run this script!")
        return 1
        
    print("✅ Model loaded successfully into memory!")
    
    # Check image argument
    img_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_tree.jpg"
    if not os.path.exists(img_path):
        from PIL import Image
        img = Image.new("RGB", (224, 224), color=(34, 139, 34))
        img.save(img_path)
        
    print(f"\n[2/2] Running inference on: {img_path}")
    result = analyze_with_juppy44(img_path)
    print("\nResult:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
