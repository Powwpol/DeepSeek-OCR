# DeepSeek OCR MCP Server

A Model Context Protocol (MCP) server that exposes [DeepSeek OCR](https://github.com/deepseek-ai/DeepSeek-OCR) functionality to any MCP-compatible AI model or application.

## Overview

This MCP server allows any model (Claude, GPT, etc.) to perform advanced OCR operations using DeepSeek's state-of-the-art OCR model. It provides tools for processing images and PDFs with various OCR capabilities.

## Features

- 🖼️ **Image OCR**: Process single images with advanced OCR
- 📄 **PDF OCR**: Process multi-page PDF documents
- 🎯 **Multiple Prompt Templates**: Pre-configured templates for different OCR tasks
- ⚡ **High Performance**: Powered by vLLM for fast inference
- 🔧 **Flexible Configuration**: Support for custom prompts and cropping modes

## Installation

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (recommended)
- 16GB+ GPU memory (for optimal performance)

### Setup

1. **Clone the repository** (if you haven't already):
```bash
git clone <your-repo-url>
cd <repo-directory>
```

2. **Install dependencies**:
```bash
pip install -r mcp_requirements.txt
```

3. **Download the DeepSeek OCR model**:
The model will be automatically downloaded from HuggingFace on first use, or you can pre-download it:
```bash
huggingface-cli download deepseek-ai/DeepSeek-OCR
```

4. **Set the model path** (optional):
```bash
export DEEPSEEK_OCR_MODEL_PATH="deepseek-ai/DeepSeek-OCR"
# Or point to a local path:
# export DEEPSEEK_OCR_MODEL_PATH="/path/to/local/model"
```

## Configuration

### MCP Server Configuration

Add this to your MCP settings file (e.g., `claude_desktop_config.json` for Claude Desktop):

```json
{
  "mcpServers": {
    "deepseek-ocr": {
      "command": "python",
      "args": ["/path/to/workspace/deepseek_ocr_mcp_server.py"],
      "env": {
        "DEEPSEEK_OCR_MODEL_PATH": "deepseek-ai/DeepSeek-OCR",
        "CUDA_VISIBLE_DEVICES": "0"
      }
    }
  }
}
```

### Environment Variables

- `DEEPSEEK_OCR_MODEL_PATH`: Path to the DeepSeek OCR model (default: `deepseek-ai/DeepSeek-OCR`)
- `CUDA_VISIBLE_DEVICES`: GPU device ID to use (default: `0`)

## Available Tools

### 1. `process_image_ocr`

Process a single image with OCR.

**Parameters:**
- `image_source` (string, required): File path or base64-encoded image
- `image_type` (string): Either `"path"` or `"base64"` (default: `"path"`)
- `prompt_template` (string): OCR prompt template to use (default: `"document_markdown"`)
- `custom_prompt` (string, optional): Custom prompt when using `"custom"` template
- `crop_mode` (boolean): Enable intelligent cropping for large images (default: `true`)

**Example:**
```json
{
  "image_source": "/path/to/image.jpg",
  "image_type": "path",
  "prompt_template": "document_markdown",
  "crop_mode": true
}
```

### 2. `process_pdf_ocr`

Process a PDF document with OCR (all pages).

**Parameters:**
- `pdf_path` (string, required): Path to the PDF file
- `prompt_template` (string): OCR prompt template to use (default: `"document_markdown"`)
- `custom_prompt` (string, optional): Custom prompt when using `"custom"` template
- `crop_mode` (boolean): Enable intelligent cropping for large images (default: `true`)

**Example:**
```json
{
  "pdf_path": "/path/to/document.pdf",
  "prompt_template": "document_markdown",
  "crop_mode": true
}
```

### 3. `list_prompt_templates`

List all available prompt templates.

**Parameters:** None

## Prompt Templates

The server includes several pre-configured prompt templates optimized for different OCR tasks:

- **`document_markdown`**: Convert documents to markdown format with grounding
  - Best for: Documents, reports, articles
  - Prompt: `<image>\n<|grounding|>Convert the document to markdown.`

- **`document_ocr`**: General document OCR with grounding
  - Best for: Structured documents
  - Prompt: `<image>\n<|grounding|>OCR this image.`

- **`free_ocr`**: Free-form OCR without grounding
  - Best for: Simple text extraction
  - Prompt: `<image>\nFree OCR.`

- **`parse_figure`**: Parse figures and diagrams
  - Best for: Charts, graphs, diagrams
  - Prompt: `<image>\nParse the figure.`

- **`describe_image`**: Detailed image description
  - Best for: General image understanding
  - Prompt: `<image>\nDescribe this image in detail.`

- **`custom`**: Custom prompt
  - Use your own prompt text
  - Prompt: `<image>\n{your_custom_prompt}`

## Usage Examples

### Using with Claude Desktop

Once configured, you can ask Claude to use the OCR tools:

```
User: "Can you OCR this document for me?"
[Attach an image]

Claude will automatically use the process_image_ocr tool to extract text.
```

### Using with Other MCP Clients

```python
# Example with MCP Python client
import asyncio
from mcp import ClientSession

async def ocr_example():
    async with ClientSession() as session:
        # Process an image
        result = await session.call_tool(
            "process_image_ocr",
            {
                "image_source": "/path/to/image.jpg",
                "prompt_template": "document_markdown"
            }
        )
        print(result)

asyncio.run(ocr_example())
```

### Command Line Testing

You can test the server directly:

```bash
python deepseek_ocr_mcp_server.py
```

Then send JSON-RPC requests via stdin.

## Performance Tuning

### GPU Memory Optimization

Adjust these settings in `deepseek_ocr_mcp_server.py`:

```python
DEFAULT_GPU_MEMORY_UTILIZATION = 0.75  # Reduce if OOM errors occur
DEFAULT_MAX_CONCURRENCY = 4  # Lower for less memory usage
```

### Cropping Configuration

For large images, the server automatically crops them into tiles for better OCR quality. Configure in `DeepSeek-OCR-master/DeepSeek-OCR-vllm/config.py`:

```python
BASE_SIZE = 1024  # Base resolution
IMAGE_SIZE = 640  # Tile size
CROP_MODE = True  # Enable/disable cropping
MIN_CROPS = 2     # Minimum number of crops
MAX_CROPS = 6     # Maximum number of crops (reduce for less memory)
```

## Troubleshooting

### Common Issues

**1. Out of Memory (OOM) Errors**
- Reduce `DEFAULT_GPU_MEMORY_UTILIZATION` in the server
- Lower `MAX_CROPS` in config.py
- Reduce `DEFAULT_MAX_CONCURRENCY`

**2. Model Download Issues**
- Ensure you have HuggingFace access
- Pre-download the model using `huggingface-cli`
- Check your internet connection

**3. CUDA Errors**
- Verify CUDA version compatibility
- Set `CUDA_VISIBLE_DEVICES` to a valid GPU ID
- Check GPU driver installation

**4. Slow Performance**
- Use crop_mode=False for small images
- Reduce image resolution before processing
- Consider using a more powerful GPU

### Debug Mode

Enable verbose logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
python deepseek_ocr_mcp_server.py
```

## Architecture

```
┌─────────────────┐
│  MCP Client     │ (Claude, GPT, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MCP Server     │ (deepseek_ocr_mcp_server.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  vLLM Engine    │ (Fast inference)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DeepSeek OCR    │ (Model)
│  - SAM Vision   │
│  - CLIP Vision  │
│  - LLM Decoder  │
└─────────────────┘
```

## Advanced Configuration

### Custom Model Path

```python
# In deepseek_ocr_mcp_server.py
DEFAULT_MODEL_PATH = "/your/custom/model/path"
```

### Custom Sampling Parameters

```python
# Modify in get_llm() function
_sampling_params = SamplingParams(
    temperature=0.1,  # Increase for more variety
    max_tokens=16384,  # Increase for longer outputs
    top_p=0.95,
    # ... other parameters
)
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project follows the license of the DeepSeek OCR model and the MCP protocol.

## Acknowledgments

- [DeepSeek AI](https://github.com/deepseek-ai) for the amazing OCR model
- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol
- [vLLM](https://github.com/vllm-project/vllm) for fast inference

## Support

For issues related to:
- **MCP Server**: Open an issue in this repository
- **DeepSeek OCR Model**: Check the [official repository](https://github.com/deepseek-ai/DeepSeek-OCR)
- **vLLM**: Visit the [vLLM repository](https://github.com/vllm-project/vllm)
