"""
Example usage of DeepSeek OCR MCP Server

This script demonstrates how to use the MCP server programmatically.
"""

import json
import sys
from pathlib import Path


def print_example_request(tool_name: str, arguments: dict):
    """Print an example MCP request."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    print(f"\n{'='*60}")
    print(f"Example: {tool_name}")
    print(f"{'='*60}\n")
    print(json.dumps(request, indent=2))
    print()


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║         DeepSeek OCR MCP Server - Usage Examples         ║
╚════════════════════════════════════════════════════════════╝
""")

    # Example 1: List prompt templates
    print_example_request(
        "list_prompt_templates",
        {}
    )

    # Example 2: Process an image from file path
    print_example_request(
        "process_image_ocr",
        {
            "image_source": "/path/to/document.jpg",
            "image_type": "path",
            "prompt_template": "document_markdown",
            "crop_mode": True
        }
    )

    # Example 3: Process an image from base64
    print_example_request(
        "process_image_ocr",
        {
            "image_source": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
            "image_type": "base64",
            "prompt_template": "free_ocr",
            "crop_mode": False
        }
    )

    # Example 4: Process a PDF
    print_example_request(
        "process_pdf_ocr",
        {
            "pdf_path": "/path/to/document.pdf",
            "prompt_template": "document_markdown",
            "crop_mode": True
        }
    )

    # Example 5: Use custom prompt
    print_example_request(
        "process_image_ocr",
        {
            "image_source": "/path/to/chart.png",
            "image_type": "path",
            "prompt_template": "custom",
            "custom_prompt": "Extract all the numbers from this chart",
            "crop_mode": True
        }
    )

    print("""
╔════════════════════════════════════════════════════════════╗
║                  Available Prompt Templates                ║
╚════════════════════════════════════════════════════════════╝

1. document_markdown - Convert documents to markdown (recommended)
2. document_ocr      - General document OCR with layout
3. free_ocr          - Simple text extraction
4. parse_figure      - Parse charts, graphs, diagrams
5. describe_image    - Detailed image description
6. custom            - Use your own prompt

╔════════════════════════════════════════════════════════════╗
║                    Integration Examples                    ║
╚════════════════════════════════════════════════════════════╝

Python Client:
--------------
from mcp import ClientSession

async with ClientSession() as session:
    result = await session.call_tool(
        "process_image_ocr",
        {"image_source": "/path/to/image.jpg"}
    )
    print(result)


Claude Desktop:
---------------
Just ask: "Can you OCR this document?" and attach an image.
The MCP server will be automatically invoked.


cURL (JSON-RPC):
----------------
echo '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "process_image_ocr",
    "arguments": {
      "image_source": "/path/to/image.jpg",
      "prompt_template": "document_markdown"
    }
  }
}' | python deepseek_ocr_mcp_server.py

╔════════════════════════════════════════════════════════════╗
║                        Tips & Tricks                       ║
╚════════════════════════════════════════════════════════════╝

1. Use 'document_markdown' for best results with documents
2. Enable crop_mode for large images (>640x640)
3. Use 'free_ocr' for simple, fast text extraction
4. Process PDFs directly instead of converting to images first
5. Adjust GPU memory settings if you encounter OOM errors

For more information, see:
- QUICKSTART.md - Quick start guide
- MCP_README.md - Detailed documentation
- test_mcp_server.py - Test examples

""")


if __name__ == "__main__":
    main()
