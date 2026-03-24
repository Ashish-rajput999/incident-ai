import requests
from bs4 import BeautifulSoup
from typing import Optional
import time


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 12


def fetch_page(url: str) -> Optional[str]:
    """Fetch a URL and return cleaned text content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav, footer, scripts, styles
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Trim to reasonable size
        return text[:6000]
    except Exception as e:
        return None


def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo HTML endpoint and return list of {title, url, snippet}.
    No API key required.
    """
    results = []
    try:
        params = {"q": query, "kl": "us-en"}
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        for result in soup.select(".result__body")[:max_results]:
            title_tag = result.select_one(".result__title a")
            snippet_tag = result.select_one(".result__snippet")
            if title_tag:
                href = title_tag.get("href", "")
                # DuckDuckGo wraps URLs
                url = _extract_ddg_url(href)
                results.append(
                    {
                        "title": title_tag.get_text(strip=True),
                        "url": url,
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                    }
                )
        time.sleep(0.5)
    except Exception:
        pass
    return results


def _extract_ddg_url(href: str) -> str:
    """Extract actual URL from DuckDuckGo redirect."""
    if "uddg=" in href:
        from urllib.parse import unquote, parse_qs, urlparse
        qs = parse_qs(urlparse(href).query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return href


def scrape_solutions_from_url(url: str) -> Optional[str]:
    """Fetch page and return content relevant to solutions/fixes."""
    content = fetch_page(url)
    if not content:
        return None
    # Return first meaningful chunk
    lines = [l.strip() for l in content.split("\n") if len(l.strip()) > 40]
    return "\n".join(lines[:80])
