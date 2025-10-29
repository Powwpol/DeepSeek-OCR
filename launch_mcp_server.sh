#!/bin/bash

# DeepSeek OCR MCP Server Launcher Script

echo "=========================================="
echo "DeepSeek OCR MCP Server Launcher"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if CUDA is available (optional warning)
if ! command -v nvidia-smi &> /dev/null; then
    echo "Warning: nvidia-smi not found. GPU acceleration may not be available."
    echo "The server will attempt to use CPU, which will be significantly slower."
    echo ""
fi

# Set default environment variables if not set
export DEEPSEEK_OCR_MODEL_PATH="${DEEPSEEK_OCR_MODEL_PATH:-deepseek-ai/DeepSeek-OCR}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

echo "Configuration:"
echo "  Model Path: $DEEPSEEK_OCR_MODEL_PATH"
echo "  CUDA Device: $CUDA_VISIBLE_DEVICES"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if the MCP server file exists
SERVER_FILE="$SCRIPT_DIR/deepseek_ocr_mcp_server.py"
if [ ! -f "$SERVER_FILE" ]; then
    echo "Error: MCP server file not found: $SERVER_FILE"
    exit 1
fi

# Check if required dependencies are installed
echo "Checking dependencies..."
python3 -c "import mcp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: MCP package not installed. Please run:"
    echo "  pip install -r mcp_requirements.txt"
    exit 1
fi

python3 -c "import vllm" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: vLLM package not installed. Please run:"
    echo "  pip install -r mcp_requirements.txt"
    exit 1
fi

echo "✓ Dependencies OK"
echo ""

# Launch the server
echo "Starting DeepSeek OCR MCP Server..."
echo "Press Ctrl+C to stop the server"
echo ""
echo "=========================================="
echo ""

cd "$SCRIPT_DIR"
python3 "$SERVER_FILE"
