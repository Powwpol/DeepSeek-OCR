# Deployment Guide - DeepSeek OCR MCP Server

This guide walks you through deploying the DeepSeek OCR MCP Server from scratch.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Linux, macOS, or Windows with WSL2
- [ ] Python 3.8 or higher
- [ ] 20GB+ free disk space (for model)
- [ ] 8GB+ GPU VRAM (recommended) or powerful CPU
- [ ] Git (for cloning repositories)
- [ ] Internet connection (for model download)

## Step-by-Step Deployment

### 1. Verify Installation

Run the installation checker:

```bash
cd /workspace
python3 check_installation.py
```

This will check:
- Python version
- GPU/CUDA availability
- Required packages
- Required files

### 2. Install Dependencies

If packages are missing, install them:

```bash
pip install -r mcp_requirements.txt
```

**Note:** This may take 10-15 minutes depending on your connection.

For GPU support, ensure PyTorch is installed with CUDA:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 3. Configure Environment Variables

Set up your environment (optional):

```bash
# Model path (default: deepseek-ai/DeepSeek-OCR)
export DEEPSEEK_OCR_MODEL_PATH="deepseek-ai/DeepSeek-OCR"

# GPU device selection (default: 0)
export CUDA_VISIBLE_DEVICES="0"

# Add to your ~/.bashrc or ~/.zshrc for persistence
echo 'export DEEPSEEK_OCR_MODEL_PATH="deepseek-ai/DeepSeek-OCR"' >> ~/.bashrc
```

### 4. Download the Model (Optional)

Pre-download to avoid delays during first run:

```bash
# Using huggingface-cli
pip install huggingface-hub
huggingface-cli download deepseek-ai/DeepSeek-OCR

# Or set a custom local path
export DEEPSEEK_OCR_MODEL_PATH="/path/to/local/model"
```

### 5. Test the Server

Run the test script:

```bash
python3 test_mcp_server.py
```

Test with your own image:

```bash
python3 test_mcp_server.py /path/to/your/image.jpg
```

**Expected output:**
- List of prompt templates
- OCR result from test image
- No error messages

### 6. Launch the Server

Using the launcher script:

```bash
./launch_mcp_server.sh
```

Or directly:

```bash
python3 deepseek_ocr_mcp_server.py
```

**The server is now running and waiting for MCP requests via stdin/stdout.**

### 7. Configure Your MCP Client

#### For Claude Desktop

1. Locate your config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add the server configuration:

```json
{
  "mcpServers": {
    "deepseek-ocr": {
      "command": "python3",
      "args": ["/absolute/path/to/workspace/deepseek_ocr_mcp_server.py"],
      "env": {
        "DEEPSEEK_OCR_MODEL_PATH": "deepseek-ai/DeepSeek-OCR",
        "CUDA_VISIBLE_DEVICES": "0"
      }
    }
  }
}
```

**Important:** Use absolute paths, not relative paths!

3. Restart Claude Desktop

4. Verify the server appears in Claude's available tools

#### For Other MCP Clients

Use the configuration format appropriate for your client. The server uses standard JSON-RPC over stdio.

### 8. Test the Integration

In your MCP client (e.g., Claude), try:

```
"Can you list the available OCR prompt templates?"
```

Then attach an image and ask:

```
"Please OCR this document and convert it to markdown"
```

## Deployment Scenarios

### Scenario 1: Local Development

```bash
# Terminal 1: Run server
cd /workspace
./launch_mcp_server.sh

# Terminal 2: Test with Python
python3 test_mcp_server.py
```

### Scenario 2: Production Server

For production deployment:

1. **Create a systemd service** (Linux):

```bash
sudo nano /etc/systemd/system/deepseek-ocr-mcp.service
```

Add:

```ini
[Unit]
Description=DeepSeek OCR MCP Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/workspace
Environment="DEEPSEEK_OCR_MODEL_PATH=deepseek-ai/DeepSeek-OCR"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/usr/bin/python3 /workspace/deepseek_ocr_mcp_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable deepseek-ocr-mcp
sudo systemctl start deepseek-ocr-mcp
sudo systemctl status deepseek-ocr-mcp
```

2. **Monitor logs**:

```bash
journalctl -u deepseek-ocr-mcp -f
```

### Scenario 3: Docker Deployment (Future)

```dockerfile
# Dockerfile (example)
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip
COPY . /app
WORKDIR /app
RUN pip3 install -r mcp_requirements.txt

CMD ["python3", "deepseek_ocr_mcp_server.py"]
```

## Performance Tuning

### For Limited GPU Memory (8GB)

Edit `deepseek_ocr_mcp_server.py`:

```python
DEFAULT_GPU_MEMORY_UTILIZATION = 0.6  # Reduce from 0.75
DEFAULT_MAX_CONCURRENCY = 2  # Reduce from 4
```

Edit `DeepSeek-OCR-master/DeepSeek-OCR-vllm/config.py`:

```python
MAX_CROPS = 4  # Reduce from 6
```

### For High Performance (24GB+ GPU)

```python
DEFAULT_GPU_MEMORY_UTILIZATION = 0.9
DEFAULT_MAX_CONCURRENCY = 8
MAX_CROPS = 9
```

### For CPU-Only Systems

The server will automatically use CPU, but it will be much slower. Consider:

- Using smaller images
- Disabling cropping: `crop_mode=False`
- Processing one image at a time

## Monitoring and Maintenance

### Health Checks

Create a health check script:

```bash
#!/bin/bash
# health_check.sh

echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | \
  python3 deepseek_ocr_mcp_server.py

if [ $? -eq 0 ]; then
    echo "Server is healthy"
    exit 0
else
    echo "Server is down"
    exit 1
fi
```

### Log Monitoring

Enable verbose logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
python3 deepseek_ocr_mcp_server.py 2>&1 | tee server.log
```

### Resource Monitoring

Monitor GPU usage:

```bash
watch -n 1 nvidia-smi
```

Monitor memory:

```bash
htop
```

## Troubleshooting Deployment Issues

### Issue: "Model not found"

**Solution:**
1. Check model path: `echo $DEEPSEEK_OCR_MODEL_PATH`
2. Download model manually: `huggingface-cli download deepseek-ai/DeepSeek-OCR`
3. Use absolute path to local model

### Issue: "CUDA out of memory"

**Solution:**
1. Reduce `DEFAULT_GPU_MEMORY_UTILIZATION`
2. Reduce `MAX_CROPS` in config.py
3. Process smaller images
4. Close other GPU applications

### Issue: "Connection refused" or "Server not responding"

**Solution:**
1. Check if server is running: `ps aux | grep deepseek_ocr_mcp_server`
2. Check for port conflicts
3. Review server logs for errors
4. Restart the server

### Issue: "Slow performance"

**Solution:**
1. Ensure GPU is being used: `nvidia-smi`
2. Reduce image resolution before OCR
3. Use `crop_mode=False` for small images
4. Check GPU utilization is >80%

### Issue: "Import errors"

**Solution:**
1. Reinstall dependencies: `pip install -r mcp_requirements.txt --force-reinstall`
2. Check Python version: `python3 --version`
3. Verify virtual environment if used

## Security Considerations

1. **File Access**: Server can access any file the Python process can read
2. **GPU Resources**: Server has exclusive GPU access when running
3. **Network**: No network access required after model download
4. **Permissions**: Run with minimal necessary permissions

**Recommendations:**
- Run in a dedicated user account
- Restrict file access to necessary directories
- Use firewall rules if exposing remotely
- Keep dependencies updated

## Backup and Recovery

### Backup Critical Files

```bash
tar -czf deepseek-ocr-mcp-backup.tar.gz \
    deepseek_ocr_mcp_server.py \
    launch_mcp_server.sh \
    test_mcp_server.py \
    mcp_requirements.txt \
    *.md \
    example_mcp_config.json
```

### Recovery

```bash
tar -xzf deepseek-ocr-mcp-backup.tar.gz
pip install -r mcp_requirements.txt
./launch_mcp_server.sh
```

## Updating the Server

To update to a newer version:

```bash
# Backup current version
cp deepseek_ocr_mcp_server.py deepseek_ocr_mcp_server.py.bak

# Update the file
# ... make changes ...

# Test
python3 test_mcp_server.py

# If successful, restart production server
sudo systemctl restart deepseek-ocr-mcp  # If using systemd
```

## Production Checklist

Before going to production:

- [ ] All tests pass: `python3 test_mcp_server.py`
- [ ] Installation check passes: `python3 check_installation.py`
- [ ] GPU/CUDA working correctly
- [ ] Model downloaded and accessible
- [ ] MCP client configured correctly
- [ ] Logs directory created and writable
- [ ] Monitoring setup (GPU, memory, logs)
- [ ] Backup procedures in place
- [ ] Documentation reviewed
- [ ] Performance tuned for your hardware

## Next Steps After Deployment

1. **Test thoroughly** with various image types
2. **Monitor performance** for the first few days
3. **Adjust settings** based on usage patterns
4. **Set up alerts** for failures
5. **Document** your specific configuration
6. **Train users** on available templates and features

## Support Resources

- **Installation Issues**: Check `check_installation.py` output
- **Configuration Help**: See `example_mcp_config.json`
- **Usage Examples**: Run `python3 examples_usage.py`
- **Quick Start**: Read `QUICKSTART.md`
- **Full Documentation**: Read `MCP_README.md`

## Deployment Complete! 🎉

Your DeepSeek OCR MCP Server is now deployed and ready to use!

Test it by asking your AI assistant to OCR a document.

---

**Remember:** The server runs as a stdin/stdout process, so it should be launched by your MCP client, not run standalone (unless testing).
