"""
Agent 2: Solution Research Agent
Primary source: Real web search + scraping (NO LLM as primary research source)
LLM is ONLY used to parse/summarize scraped content into structured output.
Input : LogAnalysisOutput
Output: ResearchOutput (Pydantic)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.schemas import LogAnalysisOutput, ResearchOutput, Solution
from services.scraper import search_duckduckgo, scrape_solutions_from_url
from services.llm import call_llm_json
from config import FALLBACK_SOURCES


# Trusted technical sources to try first (always reliable)
TRUSTED_SOURCES = [
    "https://docs.sqlalchemy.org/en/20/core/pooling.html",
    "https://www.postgresql.org/docs/current/runtime-config-connection.html",
    "https://docs.gunicorn.org/en/stable/settings.html",
    "https://www.nginx.com/blog/avoiding-top-10-nginx-configuration-mistakes/",
]


def _build_search_queries(root_cause: str) -> list[str]:
    """Generate targeted search queries from the root cause."""
    base = root_cause.lower()
    queries = []

    if "pool" in base or "connection" in base:
        queries += [
            "SQLAlchemy QueuePool exhausted fix production",
            "PostgreSQL max connections exceeded solution",
            "SQLAlchemy connection pool leak detection fix",
        ]
    if "gunicorn" in base or "worker" in base or "timeout" in base:
        queries += [
            "Gunicorn worker timeout fix connection pool",
            "gunicorn worker crash database connection exhaustion",
        ]
    if "nginx" in base or "upstream" in base or "504" in base:
        queries += [
            "nginx 504 gateway timeout upstream fix",
            "nginx upstream timed out connection refused fix",
        ]

    # Always add a generic query derived from the root cause
    keywords = " ".join(root_cause.split()[:8])
    queries.append(f"{keywords} fix solution site:stackoverflow.com OR site:docs.sqlalchemy.org")

    return queries[:4]  # Limit to 4 queries


def _search_web(queries: list[str]) -> list[dict]:
    """Run queries through DuckDuckGo, collect unique results."""
    all_results = []
    seen_urls = set()
    for query in queries:
        results = search_duckduckgo(query, max_results=4)
        for r in results:
            if r["url"] not in seen_urls and r["url"].startswith("http"):
                seen_urls.add(r["url"])
                all_results.append(r)
    return all_results[:8]


def _scrape_sources(search_results: list[dict]) -> list[dict]:
    """Scrape content from search results + trusted sources."""
    scraped = []

    # Prioritize trusted technical sources
    for url in TRUSTED_SOURCES[:2]:
        content = scrape_solutions_from_url(url)
        if content:
            scraped.append({"url": url, "content": content, "title": url.split("/")[2]})

    # Scrape from web search results
    for result in search_results[:4]:
        content = scrape_solutions_from_url(result["url"])
        if content:
            scraped.append({
                "url": result["url"],
                "content": content,
                "title": result.get("title", result["url"]),
            })

    return scraped[:5]


PARSE_PROMPT = """You are analyzing scraped technical documentation and articles to extract solutions.

ROOT CAUSE: {root_cause}

SCRAPED SOURCES:
{sources_text}

Based ONLY on the scraped content above (not your general knowledge), extract up to 4 concrete solutions.
For each solution, provide:
- A clear title
- Step-by-step actions (as a string)
- Pros of this approach
- Cons or risks
- The source URL

Also recommend the single best solution for immediate production use.

Return this exact JSON:
{{
  "solutions": [
    {{
      "title": "Solution title",
      "steps": "Step 1: ...\nStep 2: ...\nStep 3: ...",
      "pros": "...",
      "cons": "...",
      "source": "https://..."
    }}
  ],
  "recommended": "Title of the recommended solution and why in 2 sentences."
}}
"""


def run(agent1_output: LogAnalysisOutput) -> ResearchOutput:
    """
    Args:
        agent1_output: Output from Log Analysis Agent
    Returns:
        ResearchOutput
    """
    root_cause = agent1_output.suspected_root_cause
    queries = _build_search_queries(root_cause)

    print(f"  [Research] Generated {len(queries)} search queries")
    search_results = _search_web(queries)
    print(f"  [Research] Found {len(search_results)} web results")

    scraped = _scrape_sources(search_results)
    print(f"  [Research] Scraped {len(scraped)} pages")

    # Build sources text for LLM parsing
    sources_text = ""
    for i, s in enumerate(scraped, 1):
        sources_text += f"\n--- SOURCE {i}: {s['title']} ({s['url']}) ---\n{s['content'][:2000]}\n"

    if not scraped:
        # Fallback: use predefined solutions based on keywords
        print("  [Research] WARNING: No sources scraped. Using built-in fallback solutions.")
        return _fallback_solutions(root_cause, queries)

    # LLM only used to PARSE and STRUCTURE scraped content
    prompt = PARSE_PROMPT.format(root_cause=root_cause, sources_text=sources_text)
    result = call_llm_json(prompt)

    # Inject search_queries_used
    result["search_queries_used"] = queries
    return ResearchOutput(**result)


def _fallback_solutions(root_cause: str, queries: list[str]) -> ResearchOutput:
    """Pre-defined solutions when web is unavailable."""
    solutions = [
        Solution(
            title="Increase SQLAlchemy Connection Pool Size",
            steps=(
                "Step 1: Locate your SQLAlchemy engine configuration.\n"
                "Step 2: Increase pool_size (e.g., pool_size=30, max_overflow=10).\n"
                "Step 3: Increase PostgreSQL max_connections in postgresql.conf.\n"
                "Step 4: Restart PostgreSQL and your application.\n"
                "Step 5: Monitor pool metrics."
            ),
            pros="Immediate relief; minimal code change.",
            cons="Does not fix underlying leaks; requires PostgreSQL restart.",
            source="https://docs.sqlalchemy.org/en/20/core/pooling.html",
        ),
        Solution(
            title="Fix DB Session Leak in Rebalance Service",
            steps=(
                "Step 1: Audit portfolio/rebalance_service.py:118 for missing session.close().\n"
                "Step 2: Wrap all DB calls in 'with SessionLocal() as session:' context managers.\n"
                "Step 3: Add pool_pre_ping=True to engine to recycle stale connections.\n"
                "Step 4: Deploy fix and monitor checked_out_connections metric."
            ),
            pros="Fixes root cause; permanent solution.",
            cons="Requires code review and deployment.",
            source="https://docs.sqlalchemy.org/en/20/orm/session_basics.html",
        ),
        Solution(
            title="Restart Application Workers Immediately",
            steps=(
                "Step 1: Perform rolling restart of Gunicorn workers.\n"
                "Step 2: Command: kill -HUP $(cat gunicorn.pid)\n"
                "Step 3: Verify connection pool drains after restart.\n"
                "Step 4: Apply permanent code fix before next deployment."
            ),
            pros="Immediate recovery; clears leaked connections.",
            cons="Temporary; issue will recur without code fix.",
            source="https://docs.gunicorn.org/en/stable/signals.html",
        ),
    ]
    return ResearchOutput(
        solutions=solutions,
        recommended=(
            "Fix DB Session Leak in Rebalance Service: This addresses the root cause directly. "
            "Combine with immediate worker restart for rapid recovery."
        ),
        search_queries_used=queries,
    )


if __name__ == "__main__":
    from models.schemas import LogAnalysisOutput
    sample = LogAnalysisOutput(
        suspected_root_cause="SQLAlchemy QueuePool exhausted due to DB session leak in rebalance_service.py",
        evidence=["QueuePool limit of size 20 overflow 5 reached"],
        confidence=0.92,
        alternate_hypotheses=["PostgreSQL max_connections too low"],
        affected_endpoints=["/api/v1/portfolio/summary", "/api/v1/orders/rebalance"],
        timeline_summary="Pool exhausted at 11:41. Workers crashed by 11:42.",
    )
    import json
    out = run(sample)
    print(json.dumps(out.model_dump(), indent=2))
