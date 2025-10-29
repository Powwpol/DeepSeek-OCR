import os
import sys
import tempfile
from typing import Optional, Dict, Any, List

# Lazy imports inside functions to avoid heavy deps at import-time

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:  # pragma: no cover
    # Allow module import even if mcp isn't installed yet
    FastMCP = None  # type: ignore


APP_NAME = "deepseek-ocr-mcp"
DEFAULT_MODEL_PATH = os.environ.get("DEESEEK_OCR_MODEL", "deepseek-ai/DeepSeek-OCR")

# Reasonable defaults aligned with repo's config.py
DEFAULT_BASE_SIZE = int(os.environ.get("DEESEEK_OCR_BASE_SIZE", "1024"))
DEFAULT_IMAGE_SIZE = int(os.environ.get("DEESEEK_OCR_IMAGE_SIZE", "640"))
DEFAULT_CROP_MODE = os.environ.get("DEESEEK_OCR_CROP_MODE", "true").lower() in {"1", "true", "yes"}


# Global singletons (lazy)
_MODEL = None
_TOKENIZER = None
_DEVICE = None
_DTYPE = None


def _select_device(requested: Optional[str] = None) -> str:
    try:
        import torch  # noqa: WPS433
    except Exception:
        return "cpu"

    if requested in {"cpu", "cuda"}:
        if requested == "cuda" and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    # auto
    return "cuda" if torch.cuda.is_available() else "cpu"


def _select_dtype(device: str):
    try:
        import torch  # noqa: WPS433
    except Exception:
        return None

    if device == "cuda":
        # Prefer bf16 if supported, else fp16, else fp32
        if getattr(torch.cuda, "is_bf16_supported", lambda: False)():
            return torch.bfloat16
        return torch.float16
    return torch.float32


def _ensure_model_loaded(
    model_path: str,
    device: Optional[str] = None,
) -> None:
    global _MODEL, _TOKENIZER, _DEVICE, _DTYPE

    if _MODEL is not None and _TOKENIZER is not None:
        return

    from transformers import AutoModel, AutoTokenizer  # noqa: WPS433

    resolved_device = _select_device(device)
    resolved_dtype = _select_dtype(resolved_device)

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_path,
        trust_remote_code=True,
        use_safetensors=True,
    )

    # Move to device and dtype where possible
    try:
        model = model.to(dtype=resolved_dtype, device=resolved_device)
    except Exception:
        # Fallback: at least eval mode
        pass
    model = model.eval()

    _MODEL = model
    _TOKENIZER = tokenizer
    _DEVICE = resolved_device
    _DTYPE = resolved_dtype


def _run_infer_on_image(
    image_path: str,
    prompt: str,
    output_dir: Optional[str],
    base_size: int,
    image_size: int,
    crop_mode: bool,
    test_compress: bool = True,
    save_results: bool = False,
) -> Dict[str, Any]:
    """Runs model.infer on a single image path and returns outputs.

    Returns a dict with keys: text (str), saved_files (List[str]).
    """
    assert _MODEL is not None and _TOKENIZER is not None, "Model not loaded"

    # Ensure output directory exists if saving
    saved_files: List[str] = []
    if save_results and output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Many community weights expose a custom .infer() via trust_remote_code
    # Signature (per repo example):
    # infer(tokenizer, prompt, image_file, output_path, base_size, image_size, crop_mode, test_compress, save_results)
    try:
        result = _MODEL.infer(  # type: ignore[attr-defined]
            _TOKENIZER,
            prompt=prompt,
            image_file=image_path,
            output_path=output_dir or "",
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode,
            test_compress=test_compress,
            save_results=save_results,
        )
    except AttributeError as exc:
        raise RuntimeError(
            "Loaded model does not expose an infer() method. Ensure trust_remote_code is supported for this model."
        ) from exc

    # If results were saved by the model code, try to locate common files
    if save_results and output_dir:
        for candidate in ("result.mmd", "result_ori.mmd", "result_with_boxes.jpg"):
            p = os.path.join(output_dir, candidate)
            if os.path.exists(p):
                saved_files.append(p)

    # Prefer returned text if any, else try reading result.mmd
    text_out: Optional[str] = None
    if isinstance(result, str) and result.strip():
        text_out = result
    elif save_results and output_dir:
        mmd_path = os.path.join(output_dir, "result.mmd")
        if os.path.exists(mmd_path):
            try:
                with open(mmd_path, "r", encoding="utf-8") as fh:
                    text_out = fh.read()
            except Exception:
                text_out = None

    return {"text": text_out or "", "saved_files": saved_files}


# Initialize MCP app
if FastMCP is not None:
    app = FastMCP(APP_NAME)
else:  # pragma: no cover
    app = None  # type: ignore


if app is not None:

    @app.tool()
    def ocr_image(
        image_path: str,
        prompt: str = "<image>\n<|grounding|>Convert the document to markdown.",
        model_path: str = DEFAULT_MODEL_PATH,
        device: Optional[str] = None,
        output_dir: Optional[str] = None,
        base_size: int = DEFAULT_BASE_SIZE,
        image_size: int = DEFAULT_IMAGE_SIZE,
        crop_mode: bool = DEFAULT_CROP_MODE,
        save_results: bool = False,
    ) -> dict:
        """
        OCR a single image to markdown/text using DeepSeek-OCR.

        - image_path: Path to an image file (.jpg/.png/...)
        - prompt: Prompt to guide OCR (include <image> token if image-aware)
        - model_path: HuggingFace model id or local path
        - device: 'auto' (default), 'cuda', or 'cpu'
        - output_dir: If provided and save_results=True, writes result files there
        - base_size, image_size, crop_mode: Model preprocessor controls
        - save_results: If true, save result.mmd and any visualization assets
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        _ensure_model_loaded(model_path=model_path, device=device)

        result = _run_infer_on_image(
            image_path=image_path,
            prompt=prompt,
            output_dir=output_dir,
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode,
            test_compress=True,
            save_results=save_results,
        )
        return result

    @app.tool()
    def ocr_pdf(
        pdf_path: str,
        prompt: str = "<image>\n<|grounding|>Convert the document to markdown.",
        model_path: str = DEFAULT_MODEL_PATH,
        device: Optional[str] = None,
        output_dir: Optional[str] = None,
        base_size: int = DEFAULT_BASE_SIZE,
        image_size: int = DEFAULT_IMAGE_SIZE,
        crop_mode: bool = DEFAULT_CROP_MODE,
        save_results: bool = False,
        dpi: int = 144,
    ) -> dict:
        """
        OCR a PDF by rasterizing pages to images and running DeepSeek-OCR.

        Returns combined markdown and list of per-page outputs.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        _ensure_model_loaded(model_path=model_path, device=device)

        # Prepare temp dir for page images if no output_dir given
        tmp_dir = None
        page_img_dir = output_dir
        if not page_img_dir:
            tmp_dir = tempfile.TemporaryDirectory()
            page_img_dir = tmp_dir.name
        os.makedirs(page_img_dir, exist_ok=True)

        try:
            import fitz  # PyMuPDF  # noqa: WPS433
            from PIL import Image  # noqa: WPS433
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("PyMuPDF and Pillow are required for PDF OCR") from exc

        # Rasterize PDF
        doc = fitz.open(pdf_path)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        combined_text: List[str] = []
        page_results: List[Dict[str, Any]] = []

        for page_index in range(doc.page_count):
            page = doc[page_index]
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_path = os.path.join(page_img_dir, f"page_{page_index+1}.png")
            pix.save(img_path)

            res = _run_infer_on_image(
                image_path=img_path,
                prompt=prompt,
                output_dir=output_dir,
                base_size=base_size,
                image_size=image_size,
                crop_mode=crop_mode,
                test_compress=True,
                save_results=save_results,
            )
            page_results.append({"page": page_index + 1, **res})
            combined_text.append(res.get("text", ""))

        try:
            doc.close()
        except Exception:
            pass

        if tmp_dir is not None:
            tmp_dir.cleanup()

        return {"text": "\n\n<--- Page Split --->\n\n".join(combined_text), "pages": page_results}

    @app.tool()
    def health() -> dict:
        """Return server and model status."""
        return {
            "app": APP_NAME,
            "model_loaded": bool(_MODEL is not None),
            "device": _DEVICE,
        }


def main() -> None:
    if app is None:
        print(
            "The 'mcp' package is not installed. Please add 'mcp' to requirements and install it.",
            file=sys.stderr,
        )
        sys.exit(1)
    app.run()


if __name__ == "__main__":
    main()
