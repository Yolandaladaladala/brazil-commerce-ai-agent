from __future__ import annotations
import pandas as pd
from typing import Dict, Any
from llm import chat

NUMERIC_FIELDS = [
    "followers", "avg_views", "engagement_rate", "gmv_30d", "fee_brl"
]

def load_creator_file(file) -> pd.DataFrame:
    name = getattr(file, "name", "")
    if name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

def score_creators(df: pd.DataFrame, category: str, budget: float | None = None) -> pd.DataFrame:
    x = df.copy()

    for c in NUMERIC_FIELDS:
        if c in x.columns:
            x[c] = pd.to_numeric(x[c], errors="coerce")

    score = pd.Series(50.0, index=x.index)

    if "category" in x.columns:
        score += x["category"].astype(str).str.lower().str.contains(category.lower(), regex=False).astype(float) * 20

    if "engagement_rate" in x.columns:
        er = x["engagement_rate"].fillna(0)
        if er.max() <= 1:
            er = er * 100
        score += er.clip(0, 10) * 2

    if "gmv_30d" in x.columns:
        g = x["gmv_30d"].fillna(0)
        if g.max() > 0:
            score += (g / g.max()) * 15

    if budget and "fee_brl" in x.columns:
        fee = x["fee_brl"]
        score += (fee <= budget).fillna(False).astype(float) * 10
        score -= (fee > budget).fillna(False).astype(float) * 10

    x["fit_score"] = score.clip(0, 100).round(1)
    return x.sort_values("fit_score", ascending=False)

def explain_creator_fit(
    shortlisted: pd.DataFrame,
    campaign_id: str,
    product: str,
    objective: str,
    approved_brief: str,
) -> str:
    cols = [c for c in [
        "creator_id", "display_name", "platform", "category",
        "followers", "avg_views", "engagement_rate",
        "gmv_30d", "fee_brl", "source", "source_date", "fit_score"
    ] if c in shortlisted.columns]

    records = shortlisted[cols].head(10).fillna("missing").to_dict("records")

    prompt = f"""
You are the Creator & Content Operations analyst.

Campaign ID: {campaign_id}
Product/SKU: {product}
Objective: {objective}
Approved brief: {approved_brief}

CREATOR DATA (user-provided / external):
{records}

Rules:
- Do not invent creators.
- Do not invent fee, audience, conversion, GMV, or follower data.
- Missing values remain missing.
- Explain why each top creator may or may not fit.
- Identify evidence gaps before outreach.
- Require human approval before contact/contract/publishing.

Return:
1. top creator shortlist rationale
2. key missing data
3. outreach/validation checklist
4. content direction
"""
    return chat(prompt)
