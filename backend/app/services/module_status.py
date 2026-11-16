"""Presentation of actual execution evidence, including legacy unavailability."""


def module_statuses(context):
    def outcome(status, reason):
        return {'status': status, 'reason': reason}
    unavailable = outcome('UNAVAILABLE', 'Execution details were not recorded for this analysis.')
    execution = context.module_execution
    image = execution.get('image_artifact_detector', unavailable)
    raw = context.raw_ml_prediction or {}
    ml_status = raw.get('status')
    ml = outcome('COMPLETED' if ml_status == 'SUCCESS' else 'PARTIAL' if ml_status == 'DEGRADED' else 'UNAVAILABLE',
                 'Unmodified frozen-model result; source page and selection method are recorded separately.')
    ocr_summary = context.ocr_summary or {}
    if context.ocr_result is None:
        ocr = outcome(ocr_summary.get('status', 'UNAVAILABLE'), ocr_summary.get('reason', 'No executable text extraction result is available.'))
    else:
        pages = context.ocr_result.get('pages', [])
        ocr = outcome('COMPLETED' if len(pages) == context.page_count else 'PARTIAL' if pages else 'FAILED',
                      'OCR text extraction does not establish textual authenticity.')
    metadata = context.metadata or {}
    meta = outcome('COMPLETED' if metadata.get('status') == 'EXTRACTED' else 'FAILED' if metadata else 'UNAVAILABLE',
                   'Embedded metadata examined; absent metadata is not evidence of forgery.')
    compression = context.compression_qualification
    jpeg = outcome('UNAVAILABLE' if compression is None else 'COMPLETED' if compression.get('is_jpeg') else 'NOT APPLICABLE',
                   'Source JPEG DQT quality estimate; no calibrated forgery probability is implied.')
    signature = execution.get('signature_region_analyzer', unavailable)
    return {'ela': image, 'random_forest': ml, 'image_quality': image,
            'copy_move': execution.get('copy_move_region_analyzer', unavailable),
            'ocr': ocr, 'metadata': meta, 'signature_visual': signature,
            'signature_authenticity': outcome('NOT IMPLEMENTED', 'No validated reference-backed signature authenticity verification exists.'),
            'jpeg_compression': jpeg,
            'file_integrity': outcome('COMPLETED', 'Original exhibit SHA-256 verified for this retrieval.')}
