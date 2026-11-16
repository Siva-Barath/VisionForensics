"""Versioned, lossless JSON projection of forensic results, excluding raw bytes."""
import json
from datetime import datetime
from dataclasses import fields

from fastapi.encoders import jsonable_encoder

from app.pipeline.artifact import Artifact
from app.pipeline.stage_result import StageResult
from app.services.preprocessing.models import QualityMetrics, PreprocessingSummary


IDENTITY_FIELDS = {'document_id', 'job_id', 'original_filename', 'file_type', 'file_bytes', 'size_bytes', 'stored_path'}


def snapshot_context(context):
    data = {field.name: getattr(context, field.name) for field in fields(context) if field.name not in IDENTITY_FIELDS}
    data['report_ready'] = getattr(context, 'report_ready', False)
    encoded = jsonable_encoder(data)
    # Reject non-JSON forensic values rather than silently persisting NaN.
    json.dumps(encoded, allow_nan=False)
    return {'schema_version': 1, 'context': encoded}


def restore_context(context, snapshot):
    if snapshot.get('schema_version') != 1:
        raise ValueError('Unsupported forensic snapshot version')
    data = snapshot['context']
    allowed = {field.name for field in fields(context)} - IDENTITY_FIELDS
    typed_lists = {'quality_metrics': QualityMetrics, 'preprocessing_summary': PreprocessingSummary,
                   'stage_results': StageResult, 'artifacts': Artifact}
    for name, value in data.items():
        if name not in allowed and name != 'report_ready':
            continue
        if name in typed_lists:
            if name == 'artifacts':
                value = [dict(entry, created_at=datetime.fromisoformat(entry['created_at'])) for entry in value]
            value = [typed_lists[name](**entry) for entry in value]
        if name == 'copy_move_features_by_page':
            value = {int(key): item for key, item in value.items()}
        setattr(context, name, value)
    return context
