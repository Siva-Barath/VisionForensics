"""
Benchmark Report Generator.
"""
import json
from dataclasses import asdict
from .models import BenchmarkReport

class BenchmarkReportGenerator:
    def generate_json(self, report: BenchmarkReport) -> str:
        return json.dumps(asdict(report), indent=2)
