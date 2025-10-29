#!/usr/bin/env python3
"""
DeepSeek OCR MCP Server

This MCP server exposes DeepSeek OCR functionality to any MCP-compatible model.
It provides tools for processing images and PDFs with OCR capabilities.
"""

import asyncio
import base64
import json
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from PIL import Image, ImageOps
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add the DeepSeek-OCR-vllm directory to the path
DEEPSEEK_OCR_PATH = Path(__file__).parent / "DeepSeek-OCR-master" / "DeepSeek-OCR-vllm"
sys.path.insert(0, str(DEEPSEEK_OCR_PATH))

# Set environment variables
if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"
os.environ['VLLM_USE_V1'] = '0'

from vllm import LLM, SamplingParams
from vllm.model_executor.models.registry import ModelRegistry
from deepseek_ocr import DeepseekOCRForCausalLM
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor

# Register the model
ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

# Global variables for lazy initialization
_llm_instance = None
_processor = None
_sampling_params = None

# Default configurations
DEFAULT_MODEL_PATH = os.environ.get("DEEPSEEK_OCR_MODEL_PATH", "deepseek-ai/DeepSeek-OCR")
DEFAULT_BASE_SIZE = 1024
DEFAULT_IMAGE_SIZE = 640
DEFAULT_CROP_MODE = True
DEFAULT_MAX_CONCURRENCY = 4
DEFAULT_GPU_MEMORY_UTILIZATION = 0.75

# Prompt templates
PROMPT_TEMPLATES = {
    "document_markdown": "<image>\n<|grounding|>Convert the document to markdown.",
    "document_ocr": "<image>\n<|grounding|>OCR this image.",
    "free_ocr": "<image>\nFree OCR.",
    "parse_figure": "<image>\nParse the figure.",
    "describe_image": "<image>\nDescribe this image in detail.",
    "custom": "<image>\n{custom_prompt}"
}


def get_llm():
    """Lazy initialization of the LLM instance."""
    global _llm_instance, _sampling_params
    
    if _llm_instance is None:
        # Import config after path is set
        import config
        config.BASE_SIZE = DEFAULT_BASE_SIZE
        config.IMAGE_SIZE = DEFAULT_IMAGE_SIZE
        config.CROP_MODE = DEFAULT_CROP_MODE
        config.MODEL_PATH = DEFAULT_MODEL_PATH
        
        _llm_instance = LLM(
            model=DEFAULT_MODEL_PATH,
            hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
            block_size=256,
            enforce_eager=False,
            trust_remote_code=True,
            max_model_len=8192,
            swap_space=0,
            max_num_seqs=DEFAULT_MAX_CONCURRENCY,
            tensor_parallel_size=1,
            gpu_memory_utilization=DEFAULT_GPU_MEMORY_UTILIZATION,
            disable_mm_preprocessor_cache=True
        )
        
        logits_processors = [
            NoRepeatNGramLogitsProcessor(
                ngram_size=20, 
                window_size=50, 
                whitelist_token_ids={128821, 128822}
            )
        ]
        
        _sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
            include_stop_str_in_output=True,
        )
    
    return _llm_instance, _sampling_params


def get_processor():
    """Get or create the DeepSeek OCR processor."""
    global _processor
    if _processor is None:
        _processor = DeepseekOCRProcessor()
    return _processor


def load_image_from_path(image_path: str) -> Optional[Image.Image]:
    """Load an image from a file path."""
    try:
        image = Image.open(image_path)
        corrected_image = ImageOps.exif_transpose(image)
        return corrected_image.convert('RGB')
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")


def load_image_from_base64(base64_str: str) -> Optional[Image.Image]:
    """Load an image from a base64 string."""
    try:
        # Remove data URL prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',', 1)[1]
        
        image_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_data))
        corrected_image = ImageOps.exif_transpose(image)
        return corrected_image.convert('RGB')
    except Exception as e:
        raise ValueError(f"Failed to load image from base64: {e}")


def process_image_ocr_sync(
    image: Image.Image,
    prompt_template: str = "document_markdown",
    custom_prompt: Optional[str] = None,
    crop_mode: bool = DEFAULT_CROP_MODE
) -> str:
    """
    Process a single image with OCR.
    
    Args:
        image: PIL Image object
        prompt_template: One of the predefined prompt templates
        custom_prompt: Custom prompt text (used with 'custom' template)
        crop_mode: Whether to use cropping for better OCR quality
        
    Returns:
        OCR result as string
    """
    llm, sampling_params = get_llm()
    processor = get_processor()
    
    # Get the prompt
    if prompt_template == "custom" and custom_prompt:
        prompt = PROMPT_TEMPLATES["custom"].format(custom_prompt=custom_prompt)
    elif prompt_template in PROMPT_TEMPLATES:
        prompt = PROMPT_TEMPLATES[prompt_template]
    else:
        raise ValueError(f"Unknown prompt template: {prompt_template}")
    
    # Update config
    import config
    config.PROMPT = prompt
    config.CROP_MODE = crop_mode
    
    # Process the image
    image_features = processor.tokenize_with_images(
        images=[image], 
        bos=True, 
        eos=True, 
        cropping=crop_mode
    )
    
    # Create request
    request = {
        "prompt": prompt,
        "multi_modal_data": {"image": image_features},
    }
    
    # Generate
    outputs = llm.generate([request], sampling_params=sampling_params)
    
    if outputs and outputs[0].outputs:
        result = outputs[0].outputs[0].text
        
        # Clean up the result
        if '<｜end▁of▁sentence｜>' in result:
            result = result.replace('<｜end▁of▁sentence｜>', '')
        
        return result
    
    return "No output generated"


def process_pdf_ocr_sync(
    pdf_path: str,
    prompt_template: str = "document_markdown",
    custom_prompt: Optional[str] = None,
    crop_mode: bool = DEFAULT_CROP_MODE
) -> Dict[str, Any]:
    """
    Process a PDF document with OCR.
    
    Args:
        pdf_path: Path to the PDF file
        prompt_template: One of the predefined prompt templates
        custom_prompt: Custom prompt text (used with 'custom' template)
        crop_mode: Whether to use cropping for better OCR quality
        
    Returns:
        Dictionary with OCR results per page
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF is required for PDF processing. Install with: pip install PyMuPDF")
    
    llm, sampling_params = get_llm()
    processor = get_processor()
    
    # Get the prompt
    if prompt_template == "custom" and custom_prompt:
        prompt = PROMPT_TEMPLATES["custom"].format(custom_prompt=custom_prompt)
    elif prompt_template in PROMPT_TEMPLATES:
        prompt = PROMPT_TEMPLATES[prompt_template]
    else:
        raise ValueError(f"Unknown prompt template: {prompt_template}")
    
    # Update config
    import config
    config.PROMPT = prompt
    config.CROP_MODE = crop_mode
    
    # Convert PDF to images
    pdf_document = fitz.open(pdf_path)
    images = []
    
    zoom = 144 / 72.0  # DPI scaling
    matrix = fitz.Matrix(zoom, zoom)
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        
        img_data = pixmap.tobytes("png")
        img = Image.open(BytesIO(img_data))
        
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        images.append(img.convert('RGB'))
    
    pdf_document.close()
    
    # Process all images
    batch_inputs = []
    for image in images:
        image_features = processor.tokenize_with_images(
            images=[image], 
            bos=True, 
            eos=True, 
            cropping=crop_mode
        )
        batch_inputs.append({
            "prompt": prompt,
            "multi_modal_data": {"image": image_features},
        })
    
    # Generate for all pages
    outputs_list = llm.generate(batch_inputs, sampling_params=sampling_params)
    
    # Collect results
    results = {
        "total_pages": len(images),
        "pages": []
    }
    
    for page_num, output in enumerate(outputs_list):
        if output.outputs:
            content = output.outputs[0].text
            
            # Clean up the result
            if '<｜end▁of▁sentence｜>' in content:
                content = content.replace('<｜end▁of▁sentence｜>', '')
            
            results["pages"].append({
                "page_number": page_num + 1,
                "content": content
            })
        else:
            results["pages"].append({
                "page_number": page_num + 1,
                "content": "No output generated"
            })
    
    return results


# Create the MCP server
app = Server("deepseek-ocr")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available OCR tools."""
    return [
        Tool(
            name="process_image_ocr",
            description="Process a single image with DeepSeek OCR. Supports various OCR tasks including document conversion to markdown, figure parsing, and general OCR.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_source": {
                        "type": "string",
                        "description": "Either a file path or a base64-encoded image string"
                    },
                    "image_type": {
                        "type": "string",
                        "enum": ["path", "base64"],
                        "description": "Type of image source: 'path' for file path, 'base64' for base64 string",
                        "default": "path"
                    },
                    "prompt_template": {
                        "type": "string",
                        "enum": list(PROMPT_TEMPLATES.keys()),
                        "description": "Prompt template to use for OCR",
                        "default": "document_markdown"
                    },
                    "custom_prompt": {
                        "type": "string",
                        "description": "Custom prompt text (only used when prompt_template is 'custom')"
                    },
                    "crop_mode": {
                        "type": "boolean",
                        "description": "Enable cropping for better OCR quality on large images",
                        "default": True
                    }
                },
                "required": ["image_source"]
            }
        ),
        Tool(
            name="process_pdf_ocr",
            description="Process a PDF document with DeepSeek OCR. Converts all pages and returns structured results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file"
                    },
                    "prompt_template": {
                        "type": "string",
                        "enum": list(PROMPT_TEMPLATES.keys()),
                        "description": "Prompt template to use for OCR",
                        "default": "document_markdown"
                    },
                    "custom_prompt": {
                        "type": "string",
                        "description": "Custom prompt text (only used when prompt_template is 'custom')"
                    },
                    "crop_mode": {
                        "type": "boolean",
                        "description": "Enable cropping for better OCR quality on large images",
                        "default": True
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="list_prompt_templates",
            description="List all available prompt templates for OCR processing.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "list_prompt_templates":
        templates_info = []
        for key, value in PROMPT_TEMPLATES.items():
            templates_info.append(f"- **{key}**: `{value}`")
        
        return [
            TextContent(
                type="text",
                text="Available prompt templates:\n\n" + "\n".join(templates_info)
            )
        ]
    
    elif name == "process_image_ocr":
        try:
            # Extract arguments
            image_source = arguments.get("image_source")
            image_type = arguments.get("image_type", "path")
            prompt_template = arguments.get("prompt_template", "document_markdown")
            custom_prompt = arguments.get("custom_prompt")
            crop_mode = arguments.get("crop_mode", True)
            
            # Load the image
            if image_type == "path":
                image = load_image_from_path(image_source)
            elif image_type == "base64":
                image = load_image_from_base64(image_source)
            else:
                raise ValueError(f"Unknown image_type: {image_type}")
            
            # Process in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                process_image_ocr_sync,
                image,
                prompt_template,
                custom_prompt,
                crop_mode
            )
            
            return [
                TextContent(
                    type="text",
                    text=result
                )
            ]
            
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error processing image: {str(e)}"
                )
            ]
    
    elif name == "process_pdf_ocr":
        try:
            # Extract arguments
            pdf_path = arguments.get("pdf_path")
            prompt_template = arguments.get("prompt_template", "document_markdown")
            custom_prompt = arguments.get("custom_prompt")
            crop_mode = arguments.get("crop_mode", True)
            
            if not os.path.exists(pdf_path):
                raise ValueError(f"PDF file not found: {pdf_path}")
            
            # Process in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                process_pdf_ocr_sync,
                pdf_path,
                prompt_template,
                custom_prompt,
                crop_mode
            )
            
            # Format the results
            output_lines = [
                f"# PDF OCR Results",
                f"",
                f"**Total Pages:** {results['total_pages']}",
                f"",
            ]
            
            for page_data in results["pages"]:
                output_lines.append(f"## Page {page_data['page_number']}")
                output_lines.append("")
                output_lines.append(page_data["content"])
                output_lines.append("")
                output_lines.append("---")
                output_lines.append("")
            
            return [
                TextContent(
                    type="text",
                    text="\n".join(output_lines)
                )
            ]
            
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error processing PDF: {str(e)}"
                )
            ]
    
    else:
        return [
            TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )
        ]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
