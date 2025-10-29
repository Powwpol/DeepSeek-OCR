#!/usr/bin/env python3
"""
Test script for DeepSeek OCR MCP Server

This script tests the MCP server functionality without requiring a full MCP client.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the server functions
from deepseek_ocr_mcp_server import (
    process_image_ocr_sync,
    load_image_from_path,
    PROMPT_TEMPLATES
)


def test_list_prompts():
    """Test listing available prompt templates."""
    print("=" * 60)
    print("TEST: List Prompt Templates")
    print("=" * 60)
    
    print("\nAvailable prompt templates:\n")
    for key, value in PROMPT_TEMPLATES.items():
        print(f"  - {key:20s}: {value}")
    
    print("\n✓ Test passed\n")


def test_image_ocr(image_path: str, prompt_template: str = "document_markdown"):
    """Test image OCR processing."""
    print("=" * 60)
    print(f"TEST: Image OCR with template '{prompt_template}'")
    print("=" * 60)
    
    try:
        print(f"\nLoading image: {image_path}")
        image = load_image_from_path(image_path)
        print(f"Image size: {image.size}")
        
        print(f"\nProcessing with DeepSeek OCR...")
        result = process_image_ocr_sync(
            image=image,
            prompt_template=prompt_template,
            crop_mode=True
        )
        
        print(f"\n--- OCR Result ---")
        print(result)
        print(f"--- End Result ---\n")
        
        print("✓ Test passed\n")
        return result
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run tests."""
    print("\n" + "=" * 60)
    print("DeepSeek OCR MCP Server - Test Suite")
    print("=" * 60 + "\n")
    
    # Test 1: List prompts
    test_list_prompts()
    
    # Test 2: Image OCR
    # Check if there are test images available
    test_images = [
        "assets/show1.jpg",
        "assets/show2.jpg",
        "assets/show3.jpg",
        "assets/show4.jpg",
    ]
    
    available_images = [img for img in test_images if Path(img).exists()]
    
    if available_images:
        print(f"Found {len(available_images)} test images\n")
        
        # Test with first available image
        test_image_ocr(available_images[0])
        
        # Optional: Test with different prompt template
        if len(available_images) > 1:
            print("\nTesting with different prompt template...")
            test_image_ocr(available_images[1], prompt_template="free_ocr")
    else:
        print("No test images found in assets/ directory")
        print("Please provide an image path manually:")
        print("  python test_mcp_server.py /path/to/your/image.jpg")
        
        if len(sys.argv) > 1:
            image_path = sys.argv[1]
            if Path(image_path).exists():
                test_image_ocr(image_path)
            else:
                print(f"\nError: Image not found: {image_path}")
    
    print("=" * 60)
    print("Test suite completed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
