"""
Configuration for Report Generation.
"""
from typing import Dict
from pydantic import BaseModel

class ReportGenerationConfig(BaseModel):
    # Versioning
    software_name: str = "VisionForensics AI"
    software_version: str = "2.1.0"
    report_version: str = "1.0"

    # Templating
    default_template: str = "Corporate"
    supported_templates: list[str] = ["Corporate", "Academic", "Minimal", "Dark Mode"]

    # Export Settings
    include_metadata: bool = True
    include_chain_of_custody: bool = True
    image_quality: int = 95
    watermark_text: str = "CONFIDENTIAL - FORENSIC REPORT"
    
    # Validation
    strict_validation: bool = True  # Block export if validation fails
