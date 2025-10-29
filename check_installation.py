#!/usr/bin/env python3
"""
Installation checker for DeepSeek OCR MCP Server
This script verifies all requirements are met before running the server.
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_status(item, status, details=""):
    """Print a status line."""
    symbol = "✓" if status else "✗"
    status_text = "OK" if status else "FAILED"
    print(f"  [{symbol}] {item:40s} {status_text}")
    if details:
        print(f"      → {details}")


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    required = (3, 8)
    is_ok = version >= required
    details = f"Found {version.major}.{version.minor}.{version.micro}"
    if not is_ok:
        details += f" (need >= {required[0]}.{required[1]})"
    return is_ok, details


def check_cuda():
    """Check if CUDA is available."""
    try:
        result = subprocess.run(['nvidia-smi'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            # Parse GPU info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'CUDA Version:' in line:
                    cuda_version = line.split('CUDA Version:')[1].strip().split()[0]
                    return True, f"CUDA {cuda_version} available"
            return True, "CUDA available"
        else:
            return False, "nvidia-smi failed"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "nvidia-smi not found (CPU mode will be used)"


def check_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, "Installed"
    except ImportError:
        return False, "Not installed"


def check_file_exists(filepath):
    """Check if a file exists."""
    path = Path(filepath)
    return path.exists(), f"{'Found' if path.exists() else 'Missing'}: {filepath}"


def main():
    """Run all checks."""
    print_header("DeepSeek OCR MCP Server - Installation Checker")
    
    all_ok = True
    
    # Check Python version
    print("🐍 Python Environment:")
    is_ok, details = check_python_version()
    print_status("Python version", is_ok, details)
    all_ok = all_ok and is_ok
    
    # Check CUDA
    print("\n🎮 GPU Support:")
    is_ok, details = check_cuda()
    print_status("CUDA/GPU", is_ok, details)
    if not is_ok:
        print("      ⚠️  Server will run on CPU (very slow)")
    
    # Check required packages
    print("\n📦 Required Packages:")
    
    packages = [
        ("mcp", "mcp"),
        ("transformers", "transformers"),
        ("vllm", "vllm"),
        ("torch", "torch"),
        ("PIL", "PIL"),
        ("numpy", "numpy"),
        ("PyMuPDF", "fitz"),
        ("einops", "einops"),
        ("addict", "addict"),
    ]
    
    for package_name, import_name in packages:
        is_ok, details = check_package(package_name, import_name)
        print_status(package_name, is_ok, details)
        if not is_ok:
            all_ok = False
    
    # Check required files
    print("\n📄 Required Files:")
    
    files = [
        "deepseek_ocr_mcp_server.py",
        "launch_mcp_server.sh",
        "test_mcp_server.py",
        "mcp_requirements.txt",
        "MCP_README.md",
        "QUICKSTART.md",
    ]
    
    for filename in files:
        is_ok, details = check_file_exists(filename)
        print_status(filename, is_ok, details)
        if not is_ok:
            all_ok = False
    
    # Check DeepSeek OCR files
    print("\n🔍 DeepSeek OCR Components:")
    
    deepseek_files = [
        "DeepSeek-OCR-master/DeepSeek-OCR-vllm/deepseek_ocr.py",
        "DeepSeek-OCR-master/DeepSeek-OCR-vllm/config.py",
        "DeepSeek-OCR-master/DeepSeek-OCR-vllm/process/image_process.py",
    ]
    
    for filename in deepseek_files:
        is_ok, details = check_file_exists(filename)
        print_status(Path(filename).name, is_ok, details)
        if not is_ok:
            all_ok = False
    
    # Summary
    print("\n" + "="*60)
    if all_ok:
        print("  ✅ ALL CHECKS PASSED!")
        print("  You can proceed with:")
        print("    1. Test: python test_mcp_server.py")
        print("    2. Launch: ./launch_mcp_server.sh")
    else:
        print("  ⚠️  SOME CHECKS FAILED")
        print("  Please fix the issues above before proceeding.")
        print("\n  To install missing packages:")
        print("    pip install -r mcp_requirements.txt")
    print("="*60 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
