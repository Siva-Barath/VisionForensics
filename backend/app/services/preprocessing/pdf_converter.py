"""PDF processing service — converts PDF pages to images for downstream analysis."""

from pathlib import Path
from contextlib import closing

from app.core.constants import PDF_DPI, PDF_IMAGE_FORMAT
from app.core.exceptions import StorageError
from app.core.logging import get_logger

logger = get_logger(__name__)


def convert_pdf_to_images(pdf_path: Path, output_dir: Path, document_id: str) -> list[str]:
    """
    Convert each page of a PDF to a PNG image.

    Args:
        pdf_path: Path to the saved PDF file.
        output_dir: Directory where page images will be stored.
        document_id: Used to namespace the output filenames.

    Returns:
        List of relative paths to the generated page images.

    Raises:
        StorageError: if pypdfium2, pdf2image or Pillow fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    page_paths: list[str] = []

    # Priority 1: Use pypdfium2 (embedded Chromium engine, no external Poppler binary needed)
    try:
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(str(pdf_path)) as doc:
            if not len(doc):
                raise StorageError("PDF has no renderable pages")
            for idx in range(len(doc)):
                page_path = output_dir / f"{document_id}_page_{idx + 1}.{PDF_IMAGE_FORMAT.lower()}"
                with closing(doc[idx]) as page:
                    max_dim_pt = max(page.get_size())
                    if max_dim_pt <= 0:
                        raise StorageError("PDF page dimensions are invalid")
                    scale = min(2.0, 2048.0 / max_dim_pt)
                    bitmap = page.render(scale=scale)
                    try:
                        rendered = bitmap.to_pil()
                        try:
                            rendered.save(str(page_path), PDF_IMAGE_FORMAT)
                        finally:
                            rendered.close()
                    finally:
                        bitmap.close()
                page_paths.append(str(page_path))
        logger.info("Converted PDF '%s' to %d genuine page images", pdf_path.name, len(page_paths))
        return page_paths
    except ImportError:
        pass
    except Exception as exc:
        # Preserve any derived files for diagnosis, but never substitute an error
        # graphic or silently omit a page and continue forensic inference.
        raise StorageError("PDF page rendering failed; original exhibit preserved") from exc

    # Priority 2: Fallback to pdf2image
    try:
        from pdf2image import convert_from_path  # lazy import
        pages = convert_from_path(str(pdf_path), dpi=PDF_DPI, size=2048)
        for idx, page in enumerate(pages, start=1):
            page_filename = f"{document_id}_page_{idx}.{PDF_IMAGE_FORMAT.lower()}"
            page_path = output_dir / page_filename
            try:
                page.save(str(page_path), PDF_IMAGE_FORMAT)
            finally:
                page.close()
            page_paths.append(str(page_path))
            logger.debug("Saved PDF page %d → %s", idx, page_path)

        logger.info("Converted PDF '%s' → %d page(s) via pdf2image", pdf_path.name, len(pages))
        return page_paths
    except ImportError as exc:
        raise StorageError("Neither pypdfium2 nor pdf2image is available. Run: pip install pypdfium2") from exc
    except Exception as exc:
        logger.error("PDF conversion failed for '%s': %s", pdf_path, exc)
        raise StorageError(f"PDF conversion failed: {exc}") from exc
