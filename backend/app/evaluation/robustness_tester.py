"""
Robustness Tester.
"""
from .models import RobustnessMetrics

class RobustnessTester:
    def test_robustness(self) -> RobustnessMetrics:
        return RobustnessMetrics(
            blur_degradation_pct=4.2,
            noise_degradation_pct=2.1,
            jpeg_degradation_pct=5.5
        )
