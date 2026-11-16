"""
Image Artifact Detector.

Acts as an orchestrator for multiple internal CV-based analyzers.
"""
import cv2
from typing import List
import logging
import hashlib
from pathlib import Path
from app.config.settings import get_settings
from app.pipeline.artifact import Artifact

from app.pipeline.context import AnalysisContext
from app.services.forensics.base_detector import BaseDetector
from app.services.forensics.models import Evidence

from .image_analyzers import ImageAnalysisCache, ImageAnalyzerConfig
from .image_analyzers.blur_analyzer import BlurAnalyzer
from .image_analyzers.noise_analyzer import NoiseAnalyzer
from .image_analyzers.ela_analyzer import ELAAnalyzer
from .image_analyzers.edge_analyzer import EdgeAnalyzer
from .image_analyzers.illumination_analyzer import IlluminationAnalyzer
from .image_analyzers.compression_analyzer import CompressionAnalyzer
from .image_analyzers.entropy_analyzer import EntropyAnalyzer

logger = logging.getLogger(__name__)

class ImageArtifactDetector(BaseDetector):
    def __init__(self, config: ImageAnalyzerConfig = None):
        self.config = config or ImageAnalyzerConfig()
        
        # Register internal analyzers
        self.analyzers = [
            BlurAnalyzer(),
            NoiseAnalyzer(),
            ELAAnalyzer(),
            EdgeAnalyzer(),
            IlluminationAnalyzer(),
            CompressionAnalyzer(),
            EntropyAnalyzer()
        ]

    @property
    def name(self) -> str:
        return "image_artifact_detector"

    def detect(self, context: AnalysisContext) -> List[Evidence]:
        all_evidence = []
        
        if not context.preprocessed_images:
            return all_evidence
            
        for idx, path in enumerate(context.preprocessed_images):
            img = cv2.imread(path)
            
            if img is None:
                logger.warning("Failed to load preprocessed image for forensics: %s", path)
                context.add_warning(f"Image forensics could not read page {idx + 1}.")
                continue
                
            cache = ImageAnalysisCache(img)
            
            # ---- collect scalars before analyzers run so cache is warm ----
            import numpy as np

            laplacian_variance = float(np.var(cache.laplacian))

            lap_median = float(np.median(cache.laplacian))
            mad = float(np.median(np.abs(cache.laplacian - lap_median)))
            noise_sigma = float(1.4826 * mad)

            total_px = cache.canny.shape[0] * cache.canny.shape[1]
            edge_density = float(np.count_nonzero(cache.canny) / total_px) if total_px > 0 else 0.0

            bg_illum = cv2.GaussianBlur(cache.gray, (101, 101), 0)
            illumination_std = float(np.std(bg_illum))

            blur_severity = max(0.0, min(100.0, 100.0 * (1.0 - (laplacian_variance / self.config.blur_threshold)))) \
                if laplacian_variance < self.config.blur_threshold else 0.0

            # ELA scalars
            ela_region_count = 0
            ela_max_difference = 0.0
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.config.ela_quality]
            ok, encimg = cv2.imencode('.jpg', cache.original, encode_param)
            if ok:
                decimg = cv2.imdecode(encimg, 1)
                diff_gray = cv2.cvtColor(cv2.absdiff(cache.original, decimg), cv2.COLOR_BGR2GRAY)
                ela_max_difference = float(np.max(diff_gray))
                if ela_max_difference > 0:
                    scale = 255.0 / ela_max_difference
                    ela_img = cv2.convertScaleAbs(diff_gray, alpha=scale)
                else:
                    ela_img = diff_gray
                _, thresh = cv2.threshold(
                    ela_img, int(self.config.ela_threshold * 255 / 100), 255, cv2.THRESH_BINARY
                )
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                ela_region_count = sum(
                    1 for c in contours
                    if 50 < cv2.contourArea(c) < (ela_img.shape[0] * ela_img.shape[1] * 0.5)
                )
                if context.stored_path:
                    # Save the actual normalized ELA error map, not a severity
                    # illustration. This does not change the frozen scalar features.
                    try:
                        directory = Path(get_settings().heatmaps_dir) / context.document_id
                        directory.mkdir(parents=True, exist_ok=True)
                        heatmap = cv2.applyColorMap(ela_img, cv2.COLORMAP_INFERNO)
                        encoded_ok, encoded = cv2.imencode('.png', heatmap)
                        if not encoded_ok:
                            raise RuntimeError('ELA heatmap encoding failed')
                        content = encoded.tobytes()
                        path = directory / f'{context.job_id}_page_{idx}_ela.png'
                        if path.exists():
                            if path.read_bytes() != content:
                                raise RuntimeError('Derived heatmap overwrite prohibited')
                        else:
                            with path.open('xb') as output:
                                output.write(content)
                        context.register_artifact(Artifact(type='ela_heatmap', path=str(path),
                            sha256_hash=hashlib.sha256(content).hexdigest(), mime_type='image/png',
                            created_by_stage='forgery', page_index=idx,
                            description='JPEG recompression absolute difference, normalized per page; not proof of manipulation'))
                    except Exception:
                        context.add_warning(f'ELA heatmap could not be retained for page {idx + 1}.')

            # Entropy proxy (local std mean)
            blur_f = cv2.blur(cache.gray.astype(np.float32),
                              (self.config.entropy_window, self.config.entropy_window))
            sq_blur_f = cv2.blur((cache.gray.astype(np.float32) ** 2),
                                 (self.config.entropy_window, self.config.entropy_window))
            local_std = np.sqrt(np.maximum(sq_blur_f - blur_f ** 2, 0))
            entropy_score = float(np.mean(local_std))

            page_metrics: dict = {
                "page_index": idx,
                "laplacian_variance": laplacian_variance,
                "blur_severity": blur_severity,
                "noise_sigma": noise_sigma,
                "edge_density": edge_density,
                "illumination_std": illumination_std,
                "ela_region_count": ela_region_count,
                "ela_max_difference": ela_max_difference,
                "entropy_score": entropy_score,
            }
            context.image_forensics_metrics.append(page_metrics)
            # ---------------------------------------------------------------

            for analyzer in self.analyzers:
                try:
                    evidence = analyzer.analyze(idx, cache, context, self.config)
                    all_evidence.extend(evidence)
                except Exception as e:
                    logger.error("Internal analyzer %s failed on page %d: %s", analyzer.name, idx, str(e))
                    context.add_warning(f"Image analyzer {analyzer.name} failed on page {idx + 1}.")
                    
        return all_evidence
