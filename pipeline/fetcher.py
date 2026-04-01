"""HTTP fetch layer — retrieves raw content from source URLs."""

import time
from dataclasses import dataclass
import requests


@dataclass
class FetchResult:
    html: str
    status_code: int
    response_size: int
    elapsed_ms: int
    success: bool
    error: str = None


def fetch(url: str, js_rendered: bool = False, timeout: int = 30) -> FetchResult:
    """Fetch raw content from a URL. Retry once on failure."""
    headers = {
        "User-Agent": "FishOn/1.0 (fishing data aggregator; contact@fishon.app)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    for attempt in range(2):  # max 2 attempts
        try:
            start = time.time()
            resp = requests.get(url, headers=headers, timeout=timeout)
            elapsed = int((time.time() - start) * 1000)

            return FetchResult(
                html=resp.text,
                status_code=resp.status_code,
                response_size=len(resp.content),
                elapsed_ms=elapsed,
                success=resp.status_code < 400
            )
        except requests.Timeout:
            if attempt == 0:
                continue  # retry once
            return FetchResult(
                html="", status_code=0, response_size=0,
                elapsed_ms=timeout * 1000, success=False,
                error="Timeout after retry"
            )
        except requests.RequestException as e:
            if attempt == 0:
                time.sleep(1)
                continue
            return FetchResult(
                html="", status_code=0, response_size=0,
                elapsed_ms=0, success=False,
                error=str(e)
            )
