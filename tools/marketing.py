from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Dict, Iterable, List

import pandas as pd

from llm import chat


# -----------------------------------------------------------------------------
# Schema normalisation
# -----------------------------------------------------------------------------
# The Marketing module must accept real files, not only our own template.
# Keys below include the English MVP schema and common Portuguese variants.
COLUMN_ALIASES = {
    "creator_id": [
        "creator_id", "creator id", "id creator", "id do creator", "id do criador",
    ],
    "display_name": [
        "display_name", "display name", "name", "creator", "creator_name", "creator name",
        "username", "user name", "handle", "nome", "nome do criador", "criador",
    ],
    "platform": [
        "platform", "platforms", "plataforma", "plataformas", "plataforma(s)",
    ],
    "category": [
        "category", "creator_category", "creator category", "categoria", "niche", "nicho",
    ],
    "followers": [
        "followers", "follower", "followers_count", "follower count", "seguidores",
        "numero de seguidores", "número de seguidores",
    ],
    "avg_views": [
        "avg_views", "average_views", "average views", "media de views", "média de views",
        "visualizacoes medias", "visualizações médias",
    ],
    "engagement_rate": [
        "engagement_rate", "engagement rate", "engagement", "taxa de engajamento",
        "engajamento",
    ],
    "gmv_30d": [
        "gmv_30d", "gmv 30d", "gmv", "gmv_30_days", "gmv 30 days", "gmv 30 dias",
    ],
    "fee_brl": [
        "fee_brl", "creator_fee", "creator fee", "fee", "price", "quote", "quotation",
        "preco", "preço", "valor", "cachê", "cache",
    ],
    "profile_url": [
        "profile_url", "profile url", "profile link", "link perfil tiktok",
        "link perfil instagram", "link do perfil", "perfil",
    ],
    "content_url": [
        "content_url", "content url", "video_url", "video url", "link video tiktok",
        "link vídeo tiktok", "link do video", "link do vídeo",
    ],
    "product_url": [
        "product_url", "product url", "website", "website_url", "site", "link site/produto",
        "link produto", "link do produto",
    ],
    "content_focus": [
        "content_focus", "content focus", "what they teach", "o que ensina", "conteudo",
        "conteúdo", "tema", "topic",
    ],
    "mentioned_tool": [
        "mentioned_tool", "mentioned tool", "ai_tool", "ai tool",
        "modelo/ferramenta de ia mencionado", "ferramenta de ia", "modelo de ia",
    ],
    "research_status": [
        "research_status", "research status", "status", "status da pesquisa",
    ],
    "source": [
        "source", "data_source", "data source", "fonte",
    ],
    "source_date": [
        "source_date", "source date", "date", "data", "data da fonte",
    ],
}

NUMERIC_FIELDS = ["followers", "avg_views", "engagement_rate", "gmv_30d", "fee_brl"]

# High-level category vocabularies used only for deterministic relevance checks.
# These are internal matching rules, not platform taxonomies.
CATEGORY_GROUPS = {
    "pet": {
        "pet", "pets", "animal", "animals", "animais", "gato", "gatos", "cat", "cats",
        "cachorro", "cachorros", "dog", "dogs", "pet care", "petcare",
    },
    "home": {
        "home", "home living", "home & living", "living", "casa", "lar", "decor", "decoracao",
        "decoracao", "decoração", "furniture", "moveis", "móveis", "interior", "household",
    },
    "beauty": {
        "beauty", "beleza", "makeup", "maquiagem", "skincare", "skin care", "cosmetics",
        "cosmeticos", "cosméticos",
    },
    "fashion": {
        "fashion", "moda", "style", "estilo", "clothing", "apparel", "roupa", "roupas",
    },
    "food": {
        "food", "foods", "comida", "alimento", "alimentos", "culinaria", "culinária", "recipe",
        "receita", "receitas",
    },
    "fitness": {
        "fitness", "sport", "sports", "esporte", "esportes", "gym", "academia", "wellness",
        "bem estar", "bem-estar",
    },
    "tech": {
        "tech", "technology", "tecnologia", "gadget", "gadgets", "electronics", "eletronicos",
        "eletrônicos",
    },
    "ai": {
        "ai", "ia", "artificial intelligence", "inteligencia artificial", "inteligência artificial",
        "chatgpt", "generative ai", "genai", "ai content", "ai-content", "ai pack", "ai-pack",
    },
    "automotive": {
        "auto", "automotive", "car", "cars", "vehicle", "vehicles", "automotivo", "carro",
        "carros", "veiculo", "veículo", "veiculos", "veículos",
    },
}


def _plain(value: Any) -> str:
    """Lower-case, accent-insensitive text for schema/category matching."""
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[_\-/|]+", " ", text)
    text = re.sub(r"[^a-z0-9%+&. ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _alias_lookup() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        out[_plain(canonical)] = canonical
        for alias in aliases:
            out[_plain(alias)] = canonical
    return out


_ALIAS_LOOKUP = _alias_lookup()


def normalize_creator_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert heterogeneous creator files to the internal schema while preserving
    every unmapped original column. This prevents the previous failure mode in
    which Portuguese headers were silently treated as missing data.
    """
    x = df.copy()
    rename_map: Dict[str, str] = {}
    occupied = set(str(c) for c in x.columns)

    for original in x.columns:
        key = _plain(original)
        canonical = _ALIAS_LOOKUP.get(key)
        if canonical and canonical not in occupied and canonical not in rename_map.values():
            rename_map[original] = canonical
        elif canonical and str(original) == canonical:
            rename_map[original] = canonical

    x = x.rename(columns=rename_map)

    # If duplicate canonical columns exist after imperfect source files, merge
    # them left-to-right rather than dropping data.
    for canonical in COLUMN_ALIASES:
        matching = [c for c in x.columns if _plain(c) == _plain(canonical)]
        if len(matching) > 1:
            merged = x[matching[0]].copy()
            for col in matching[1:]:
                merged = merged.where(merged.notna() & (merged.astype(str).str.strip() != ""), x[col])
            x[canonical] = merged
            drop_cols = [c for c in matching if c != canonical]
            x = x.drop(columns=drop_cols, errors="ignore")

    # Create a stable creator_id if the source provides a real handle/name but no ID.
    if "creator_id" not in x.columns and "display_name" in x.columns:
        x["creator_id"] = x["display_name"].astype(str).map(
            lambda s: "CREATOR-" + re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").upper()[:48]
            if s.strip() else ""
        )

    for col in NUMERIC_FIELDS:
        if col in x.columns:
            x[col] = x[col].map(_parse_numeric)

    return x


def _parse_numeric(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    s = _plain(value)
    if not s or s in {"nan", "none", "missing", "n/a", "na", "-"}:
        return None

    multiplier = 1.0
    if re.search(r"\b(k|mil)\b", s):
        multiplier = 1_000.0
    elif re.search(r"\b(m|mi|milhao|milhoes|million)\b", s):
        multiplier = 1_000_000.0

    # Handle Brazilian decimal comma and thousands separators conservatively.
    raw = re.sub(r"[^0-9,.-]", "", s)
    if not raw:
        return None
    if "," in raw and "." in raw:
        # Assume the last separator is decimal.
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        parts = raw.split(",")
        if len(parts[-1]) in {1, 2}:
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    try:
        return float(raw) * multiplier
    except ValueError:
        return None


def load_creator_file(file) -> pd.DataFrame:
    """Read CSV/XLS/XLSX and immediately normalise the schema."""
    name = getattr(file, "name", "")
    if name.lower().endswith(".csv"):
        raw = pd.read_csv(file)
    else:
        raw = pd.read_excel(file)
    return normalize_creator_schema(raw)


# -----------------------------------------------------------------------------
# Dataset fit assessment
# -----------------------------------------------------------------------------
def _target_terms(category: str) -> set[str]:
    text = _plain(category)
    tokens = {t for t in re.split(r"\s+", text) if len(t) >= 2 and t not in {"and", "the", "de", "da", "do"}}
    terms = set(tokens)

    for group_terms in CATEGORY_GROUPS.values():
        if any(term in text for term in group_terms):
            terms.update(group_terms)
    return {_plain(t) for t in terms if _plain(t)}


def _row_relevance_text(row: pd.Series) -> str:
    fields = ["category", "content_focus", "display_name", "mentioned_tool"]
    return " | ".join(_plain(row.get(c, "")) for c in fields if c in row.index)


def _is_category_match(row: pd.Series, target_terms: set[str]) -> bool:
    if not target_terms:
        return False
    text = _row_relevance_text(row)
    if not text:
        return False
    return any(term in text for term in target_terms)


def _top_counts(series: pd.Series, n: int = 5) -> List[Dict[str, Any]]:
    clean = series.dropna().astype(str).str.strip()
    clean = clean[clean.ne("") & clean.str.lower().ne("nan")]
    counts = clean.value_counts().head(n)
    return [{"value": str(idx), "count": int(val)} for idx, val in counts.items()]


def analyse_creator_dataset(df: pd.DataFrame, target_category: str = "") -> Dict[str, Any]:
    """Profile the uploaded dataset before any creator ranking happens."""
    x = normalize_creator_schema(df)
    total = int(len(x))

    present_fields = [c for c in COLUMN_ALIASES if c in x.columns and x[c].notna().any()]
    useful_for_ranking = [
        c for c in ["display_name", "platform", "category", "followers", "avg_views",
                    "engagement_rate", "gmv_30d", "fee_brl", "content_focus", "profile_url"]
        if c in present_fields
    ]

    category_counts = _top_counts(x["category"]) if "category" in x.columns else []
    platform_counts = _top_counts(x["platform"]) if "platform" in x.columns else []

    target_terms = _target_terms(target_category)
    if target_category.strip() and total:
        match_mask = x.apply(lambda row: _is_category_match(row, target_terms), axis=1)
        matched_count = int(match_mask.sum())
    else:
        match_mask = pd.Series(False, index=x.index)
        matched_count = 0

    match_rate = matched_count / total if total else 0.0
    if not target_category.strip():
        fit_level = "NOT_ASSESSED"
    elif matched_count == 0:
        fit_level = "LOW"
    elif matched_count >= 10 or match_rate >= 0.15:
        fit_level = "HIGH"
    elif matched_count >= 3 or match_rate >= 0.05:
        fit_level = "MEDIUM"
    else:
        fit_level = "LOW"

    return {
        "rows": total,
        "present_fields": present_fields,
        "ranking_fields": useful_for_ranking,
        "top_categories": category_counts,
        "top_platforms": platform_counts,
        "target_category": target_category,
        "matched_count": matched_count,
        "match_rate": round(match_rate, 4),
        "fit_level": fit_level,
        "can_shortlist": bool(target_category.strip()) and fit_level in {"MEDIUM", "HIGH"} and matched_count > 0,
        "matched_index": x.index[match_mask].tolist(),
    }


# -----------------------------------------------------------------------------
# Deterministic ranking
# -----------------------------------------------------------------------------
def _percentile_score(s: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(s, errors="coerce")
    if numeric.notna().sum() <= 1:
        return pd.Series(0.5, index=s.index)
    return numeric.rank(pct=True, method="average").fillna(0.0)


def score_creators(df: pd.DataFrame, category: str, budget: float | None = None) -> pd.DataFrame:
    """
    Rank only creators with observed category/content relevance.

    Important: there is no default 50 score. If the uploaded pool does not fit
    the requested category, an empty shortlist is returned instead of a fake Top 10.
    """
    x = normalize_creator_schema(df)
    profile = analyse_creator_dataset(x, category)

    if not profile["can_shortlist"]:
        empty = x.iloc[0:0].copy()
        empty["fit_score"] = pd.Series(dtype=float)
        empty.attrs["dataset_profile"] = profile
        return empty

    matched = x.loc[profile["matched_index"]].copy()
    target_terms = _target_terms(category)

    matched["category_match"] = matched.apply(lambda row: _is_category_match(row, target_terms), axis=1)
    raw = pd.Series(60.0, index=matched.index)  # category relevance is mandatory and dominant
    available_weight = 60.0

    if "followers" in matched.columns and matched["followers"].notna().any():
        raw += _percentile_score(matched["followers"]) * 10.0
        available_weight += 10.0

    if "avg_views" in matched.columns and matched["avg_views"].notna().any():
        raw += _percentile_score(matched["avg_views"]) * 10.0
        available_weight += 10.0

    if "engagement_rate" in matched.columns and matched["engagement_rate"].notna().any():
        er = pd.to_numeric(matched["engagement_rate"], errors="coerce")
        if er.dropna().max() <= 1:
            er = er * 100
        raw += er.clip(lower=0, upper=10).fillna(0) / 10 * 10.0
        available_weight += 10.0

    if "gmv_30d" in matched.columns and matched["gmv_30d"].notna().any():
        raw += _percentile_score(matched["gmv_30d"]) * 5.0
        available_weight += 5.0

    if budget and "fee_brl" in matched.columns and matched["fee_brl"].notna().any():
        fee = pd.to_numeric(matched["fee_brl"], errors="coerce")
        budget_fit = fee.le(float(budget)).where(fee.notna(), False).astype(float)
        raw += budget_fit * 5.0
        available_weight += 5.0

    matched["fit_score"] = (raw / available_weight * 100).clip(0, 100).round(1)
    matched["score_data_coverage"] = round(available_weight / 100.0, 2)
    matched.attrs["dataset_profile"] = profile
    return matched.sort_values(["fit_score", "followers" if "followers" in matched.columns else "fit_score"], ascending=False)


# -----------------------------------------------------------------------------
# AI explanation
# -----------------------------------------------------------------------------
def _records_for_llm(df: pd.DataFrame, limit: int = 12) -> List[Dict[str, Any]]:
    preferred = [
        "creator_id", "display_name", "platform", "category", "followers", "avg_views",
        "engagement_rate", "gmv_30d", "fee_brl", "content_focus", "mentioned_tool",
        "profile_url", "content_url", "product_url", "research_status", "source", "source_date",
        "fit_score", "score_data_coverage",
    ]
    cols = [c for c in preferred if c in df.columns]
    if not cols:
        cols = list(df.columns[:12])
    return df[cols].head(limit).where(pd.notna(df[cols].head(limit)), "missing").to_dict("records")


def explain_creator_fit(
    shortlisted: pd.DataFrame,
    campaign_id: str,
    product: str,
    objective: str,
    approved_brief: str,
    dataset_profile: Dict[str, Any] | None = None,
    full_dataset: pd.DataFrame | None = None,
) -> str:
    """Explain either a valid shortlist or a deterministic no-match result."""
    if dataset_profile is None:
        dataset_profile = shortlisted.attrs.get("dataset_profile") if hasattr(shortlisted, "attrs") else None
    if dataset_profile is None:
        dataset_profile = analyse_creator_dataset(full_dataset if full_dataset is not None else shortlisted, "")

    if shortlisted.empty and full_dataset is not None:
        sample_source = normalize_creator_schema(full_dataset)
        sample_records = _records_for_llm(sample_source.sort_values("followers", ascending=False) if "followers" in sample_source.columns else sample_source)
    else:
        sample_records = _records_for_llm(shortlisted)

    prompt = f"""
You are the Creator & Content Operations analyst for a professional commerce team.

Internal campaign reference: {campaign_id}
Product: {product}
Objective: {objective}
Approved brief / confirmed facts only: {approved_brief or 'No additional approved product facts supplied.'}

DETERMINISTIC DATASET PROFILE:
{dataset_profile}

CREATOR RECORDS FROM THE USER-PROVIDED FILE:
{sample_records}

Non-negotiable rules:
- The uploaded file is real input. Use the creator names, categories, platforms and follower data that are actually present.
- Never say identity/category/platform/followers are missing when they are present in the records.
- Never invent creator identities, audience demographics, fees, conversion, GMV, availability, pet ownership, or historical campaign performance.
- If dataset_profile.fit_level is LOW or can_shortlist is False, DO NOT manufacture a Top Creator shortlist. State that the pool is not sufficiently relevant to the requested category and explain why.
- If a shortlist exists, distinguish observed data from interpretation and explain the limits of the deterministic score.
- Do not call someone KOC/KOL as a verified fact unless the file/source explicitly says so. If useful, you may describe an internal follower-size segment and label it as an internal heuristic.
- High-impact actions such as outreach, contract, publishing and payment require human approval.

Return a business-useful analysis with these sections:
1. Dataset Fit Assessment
2. What the current creator pool can and cannot support
3. Creator Shortlist (ONLY if deterministic category fit is sufficient; otherwise write "No qualified shortlist generated")
4. Evidence Gaps that materially affect a campaign decision
5. Recommended next data / sourcing actions
6. Content and campaign direction that can be stated from confirmed product facts only

Be concise, commercial and decision-oriented. Do not pad the answer with generic compliance checklists.
"""
    return chat(prompt)
