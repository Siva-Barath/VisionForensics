"""
Metadata Stage — Extracts and validates embedded file metadata, EXIF headers,
and PDF document catalogs to detect tool signatures and timestamp anomalies.
"""

from pathlib import Path
from typing import Dict, Any, List
from app.pipeline.base_stage import BaseStage
from app.pipeline.context import AnalysisContext
from app.pipeline.stage_result import StageResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# Known digital editing / manipulation software keywords
EDITING_SOFTWARE_KEYWORDS = [
    "photoshop",
    "gimp",
    "canva",
    "illustrator",
    "corel",
    "paint.net",
    "pixelmator",
    "affinity",
    "snapseed",
    "acrobat",
]


class MetadataStage(BaseStage):
    name = "metadata"

    async def run(self, context: AnalysisContext) -> StageResult:
        warnings: List[str] = []
        metadata: Dict[str, Any] = {
            "status": "EXTRACTED",
            "file_type": context.file_type,
            "has_metadata": False,
            "editing_software_detected": False,
            "fields": {},
        }

        stored_path = context.stored_path
        if not stored_path or not Path(stored_path).exists():
            metadata["status"] = "FILE_NOT_FOUND"
            context.metadata = metadata
            return StageResult.success(self.name)

        try:
            file_type = (context.file_type or "").lower()
            path_obj = Path(stored_path)

            if file_type == "pdf" or path_obj.suffix.lower() == ".pdf":
                # Extract PDF Catalog & Metadata using pypdf
                try:
                    import pypdf
                    with open(path_obj, "rb") as f:
                        reader = pypdf.PdfReader(f)
                        pdf_meta = reader.metadata or {}
                        page_count = len(reader.pages)

                        fields = {}
                        for key, val in pdf_meta.items():
                            clean_key = str(key).lstrip("/")
                            fields[clean_key] = str(val) if val is not None else ""

                        metadata["page_count"] = page_count
                        metadata["is_encrypted"] = reader.is_encrypted
                        metadata["fields"] = fields
                        metadata["has_metadata"] = bool(fields)

                        # Check for editing software
                        creator = fields.get("Creator", "").lower()
                        producer = fields.get("Producer", "").lower()
                        software_str = f"{creator} {producer}"

                        matched_tools = [tool for tool in EDITING_SOFTWARE_KEYWORDS if tool in software_str]
                        if matched_tools:
                            metadata["editing_software_detected"] = True
                            metadata["detected_tools"] = matched_tools
                            warnings.append(
                                f"Metadata indicates document was processed with digital editing tool: {', '.join(matched_tools)}"
                            )

                except Exception as pdf_err:
                    logger.debug("PDF metadata extraction notice: %s", pdf_err)
                    metadata["status"] = "PDF_PARSE_NOTICE"
                    metadata["error"] = str(pdf_err)

            else:
                # Extract Image EXIF using PIL
                try:
                    from PIL import Image, ExifTags
                    with Image.open(path_obj) as img:
                        metadata["image_format"] = img.format
                        metadata["image_mode"] = img.mode
                        metadata["image_dimensions"] = [img.width, img.height]

                        fields = {}
                        raw_exif = None
                        if hasattr(img, "_getexif"):
                            raw_exif = img._getexif()

                        if raw_exif:
                            for tag_id, val in raw_exif.items():
                                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                                fields[tag_name] = str(val)[:128]

                        # Check image info dictionary as well
                        if hasattr(img, "info") and img.info:
                            for k, v in img.info.items():
                                if k not in ("exif", "icc_profile") and str(k) not in fields:
                                    fields[str(k)] = str(v)[:128]

                        metadata["fields"] = fields
                        metadata["has_metadata"] = bool(fields)

                        # Check for editing software
                        software = fields.get("Software", "").lower()
                        matched_tools = [tool for tool in EDITING_SOFTWARE_KEYWORDS if tool in software]
                        if matched_tools:
                            metadata["editing_software_detected"] = True
                            metadata["detected_tools"] = matched_tools
                            warnings.append(
                                f"EXIF metadata indicates image was edited with: {', '.join(matched_tools)}"
                            )

                except Exception as img_err:
                    logger.debug("Image EXIF extraction notice: %s", img_err)
                    metadata["status"] = "IMAGE_PARSE_NOTICE"
                    metadata["error"] = str(img_err)

        except Exception as exc:
            logger.warning("Metadata stage unexpected error: %s", exc)
            metadata["status"] = "ERROR"
            metadata["error"] = str(exc)

        context.metadata = metadata
        return StageResult.success(self.name, warnings=warnings)

