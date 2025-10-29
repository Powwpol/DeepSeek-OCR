# Quick Start Guide - DeepSeek OCR MCP Server

This guide will help you get the DeepSeek OCR MCP server up and running quickly.

## Step 1: Install Dependencies

```bash
pip install -r mcp_requirements.txt
```

**Note:** This will install:
- MCP (Model Context Protocol)
- vLLM (for fast inference)
- DeepSeek OCR dependencies (transformers, PyMuPDF, etc.)

## Step 2: Configure Environment (Optional)

Set environment variables if needed:

```bash
# Optional: Set custom model path
export DEEPSEEK_OCR_MODEL_PATH="deepseek-ai/DeepSeek-OCR"

# Optional: Select GPU device
export CUDA_VISIBLE_DEVICES="0"
```

## Step 3: Test the Server

Run the test script to verify everything works:

```bash
python test_mcp_server.py
```

Or test with a specific image:

```bash
python test_mcp_server.py /path/to/your/image.jpg
```

## Step 4: Run the MCP Server

### Option A: Using the Launcher Script (Recommended)

```bash
./launch_mcp_server.sh
```

### Option B: Direct Python Execution

```bash
python deepseek_ocr_mcp_server.py
```

## Step 5: Configure Your MCP Client

### For Claude Desktop

1. Open your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the server configuration:

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

3. Restart Claude Desktop

### For Other MCP Clients

Use the `example_mcp_config.json` as a template and adapt it to your client's configuration format.

## Step 6: Use the OCR Tools

Once configured, you can ask your AI assistant to use the OCR tools:

### Example Prompts:

1. **Process an image:**
   ```
   "Can you OCR this document for me?"
   [Attach image]
   ```

2. **Process a PDF:**
   ```
   "Please extract text from this PDF: /path/to/document.pdf"
   ```

3. **List available templates:**
   ```
   "What OCR prompt templates are available?"
   ```

4. **Use a specific template:**
   ```
   "OCR this image using the 'free_ocr' template"
   [Attach image]
   ```

## Troubleshooting

### Issue: Model Download is Slow

**Solution:** Pre-download the model:
```bash
huggingface-cli download deepseek-ai/DeepSeek-OCR
```

### Issue: Out of Memory Errors

**Solution:** Reduce memory usage by editing `deepseek_ocr_mcp_server.py`:
```python
DEFAULT_GPU_MEMORY_UTILIZATION = 0.6  # Reduce from 0.75
DEFAULT_MAX_CONCURRENCY = 2  # Reduce from 4
```

### Issue: CUDA Not Available

**Solution:** The server will try to use CPU (very slow). Install CUDA toolkit:
```bash
# Check CUDA availability
nvidia-smi

# If not available, install CUDA toolkit for your system
```

### Issue: Import Errors

**Solution:** Make sure all dependencies are installed:
```bash
pip install -r mcp_requirements.txt --upgrade
```

### Issue: Path Not Found

**Solution:** Use absolute paths in your MCP client config:
```json
"args": ["/absolute/path/to/deepseek_ocr_mcp_server.py"]
```

## Performance Tips

1. **For small images (<640x640):** Disable cropping for faster processing
2. **For large documents:** Use `document_markdown` template with cropping enabled
3. **For batch processing:** Process PDFs instead of multiple images
4. **GPU memory:** Adjust based on your GPU (8GB, 16GB, 24GB, etc.)

## Next Steps

- Read the full [MCP_README.md](./MCP_README.md) for detailed documentation
- Explore different prompt templates for your use case
- Configure performance settings for your hardware
- Integrate with your favorite MCP-compatible application

## Support

For issues or questions:
1. Check the [MCP_README.md](./MCP_README.md) for detailed troubleshooting
2. Review the test script output for error messages
3. Check GPU memory usage: `nvidia-smi`
4. Enable debug logging: `export VLLM_LOGGING_LEVEL=DEBUG`

## What's Next?

Now that your MCP server is running, you can:
- Process documents and extract text
- Convert images to markdown
- Parse figures and diagrams
- Integrate OCR into your AI workflows

Happy OCR-ing! 🚀
