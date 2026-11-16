"""Protect live evidence from database/API integration tests.

Use scripts/run_isolated_backend_tests.py. Unit tests with injected sessions
remain usable without a database. No authentication bypass is installed.
"""
import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest


@pytest.fixture(autouse=True)
def require_isolated_database_for_integration_tests(request):
    source = Path(request.module.__file__).read_text(encoding='utf-8-sig')
    if 'SessionLocal' in source or 'ASGITransport' in source:
        from app.config.settings import get_settings
        expected = os.environ.get('VF_ISOLATED_TEST_DB', '')
        actual = urlsplit(get_settings().database_url).path.lstrip('/')
        if not expected.startswith('vf_test_') or actual != expected:
            pytest.fail('Integration tests require a fresh vf_test_ database; run scripts/run_isolated_backend_tests.py')
    from app.core.rate_limiter import limiter
    # Each test is a distinct scenario; counters remain enforced within it.
    with limiter._lock:
        limiter._history.clear()
        limiter._account_failures.clear()
