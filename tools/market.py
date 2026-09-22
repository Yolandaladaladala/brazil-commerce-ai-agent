from __future__ import annotations
import json
import requests
from typing import Dict, Any, List
from config import SERPER_API_KEY
from llm import chat

SOURCE_PRIORITY = [
    "Government / regulator",
    "Industry association",
    "Company disclosure",
    "Professional research institution",
    "Reliable industry media",
    "Marketplace / search evidence",
]

def _serper_search(query: str, num: int = 8) -> List[dict]:
    if not SERPER_API_KEY:
        return []
    r = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    results = []
    for x in data.get("organic", []):
        results.append({
            "title": x.get("title"),
            "link": x.get("link"),
            "snippet": x.get("snippet"),
            "source_type": "Web search evidence",
        })
    return results

def run_market_research(
    country: str,
    product: str,
    objective: str,
    platform: str = "",
    dimensions: List[str] | None = None,
) -> Dict[str, Any]:
    dimensions = dimensions or [
        "Market size & growth",
        "Competition",
        "Pricing",
        "Channels",
        "Consumer need",
        "Regulation",
    ]

    queries = [
        f"{country} {product} market size growth",
        f"{country} {product} competitors price",
        f"{country} {product} regulation ecommerce",
    ]
    if platform:
        queries.append(f"{country} {platform} {product}")

    evidence = []
    for q in queries:
        try:
            evidence.extend(_serper_search(q, 6))
        except Exception as e:
            evidence.append({
                "title": "Search error",
                "link": "",
                "snippet": str(e),
                "source_type": "Tool error",
            })

    live = len([x for x in evidence if x.get("link")]) > 0

    if not live:
        evidence = [
            {
                "title": "Demo evidence placeholder",
                "link": "",
                "snippet": "No SERPER_API_KEY configured. This is not live market evidence.",
                "source_type": "Demo only",
            }
        ]

    evidence_text = "\n".join(
        f"- {x['title']} | {x['source_type']} | {x.get('snippet','')} | {x.get('link','')}"
        for x in evidence[:16]
    )

    prompt = f"""
You are running Market & Product Intelligence.

COUNTRY: {country}
PRODUCT/CATEGORY: {product}
OBJECTIVE: {objective}
PLATFORM: {platform or "not specified"}
RESEARCH DIMENSIONS: {", ".join(dimensions)}

SOURCE PRIORITY:
{json.dumps(SOURCE_PRIORITY, ensure_ascii=False)}

EVIDENCE:
{evidence_text}

Rules:
1. Do not invent market size, sales, market share, or historical performance.
2. If evidence is insufficient, say "insufficient evidence".
3. Distinguish facts from hypothesis/inference.
4. Each important quantitative claim must have source/date/geography/definition; if unavailable, mark incomplete.
5. Return a concise decision-oriented research memo with:
   - research scope
   - findings by dimension
   - evidence gaps
   - risks/opportunities
   - next actions
"""
    analysis = chat(prompt)

    return {
        "mode": "LIVE SEARCH" if live else "DEMO SEARCH",
        "country": country,
        "product": product,
        "objective": objective,
        "dimensions": dimensions,
        "evidence": evidence,
        "analysis": analysis,
    }
