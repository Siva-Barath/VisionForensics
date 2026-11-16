"""
extract_test_features.py

Unseals and extracts the authoritative 18 active numerical features for the 
280 quarantined held-out test samples in Phase 4.
Uses the identical extraction pipeline, workers, and checkpointing logic as Phase 2.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_ROOT = _REPO_ROOT / "backend"
for p in (_REPO_ROOT, _BACKEND_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools.extract_phase2_features import run_split_extraction

def main():
    print("=== UNSEALING AND EXTRACTING TEST FEATURES (PHASE 4) ===")
    run_split_extraction("test", expected_count=280, num_workers=6)
    print("=== TEST FEATURE EXTRACTION COMPLETE ===")

if __name__ == "__main__":
    main()
