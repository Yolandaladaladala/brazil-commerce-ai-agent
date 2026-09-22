from __future__ import annotations
import pandas as pd
from typing import Dict, Any, Optional

ALIASES = {
    "sales": ["revenue", "sales", "gmv", "gross_sales"],
    "discounts": ["discounts", "discount"],
    "refunds": ["refunds", "refund"],
    "platform_fee": ["platform_fee", "platform_fees", "transaction_fee"],
    "product_cost": ["product_cost", "cogs", "cost_of_goods_sold"],
    "logistics_cost": ["logistics_cost", "fulfilment_cost", "fulfillment_cost", "shipping_cost"],
    "ad_spend": ["ad_spend", "advertising_spend", "ads_cost"],
    "creator_cost": ["creator_cost", "creator_fee", "kol_cost"],
    "software_cost": ["software_cost", "ai_cost", "livestream_cost"],
    "tax": ["tax", "tax_cost"],
    "orders": ["orders", "order_count"],
    "visits": ["visits", "sessions"],
    "clicks": ["clicks"],
    "impressions": ["impressions", "views"],
}

def load_finance_file(file) -> pd.DataFrame:
    name = getattr(file, "name", "")
    if name.lower().endswith(".csv"):
        return pd.read_csv(file)
    if name.lower().endswith(".json"):
        return pd.read_json(file)
    return pd.read_excel(file)

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x.columns = [str(c).strip().lower().replace(" ", "_") for c in x.columns]
    return x

def _find_col(columns, aliases):
    for a in aliases:
        if a in columns:
            return a
    return None

def _sum(df, col) -> Optional[float]:
    if not col:
        return None
    s = pd.to_numeric(df[col], errors="coerce")
    if s.notna().sum() == 0:
        return None
    return float(s.sum())

def analyse_finance(df: pd.DataFrame) -> Dict[str, Any]:
    x = _normalize_columns(df)
    cols = set(x.columns)

    mapping = {k: _find_col(cols, v) for k, v in ALIASES.items()}
    vals = {k: _sum(x, col) for k, col in mapping.items()}

    if vals["sales"] is None:
        raise ValueError("Missing sales/revenue/GMV. Level 1 analysis cannot run.")

    net_sales = vals["sales"] - (vals["discounts"] or 0) - (vals["refunds"] or 0)

    required_profit = ["product_cost", "logistics_cost", "ad_spend", "creator_cost"]
    missing_profit = [k for k in required_profit if vals[k] is None]

    known_costs = sum(
        vals[k] or 0 for k in
        ["platform_fee", "product_cost", "logistics_cost", "ad_spend", "creator_cost", "software_cost", "tax"]
    )

    contribution_profit = None if missing_profit else net_sales - known_costs
    contribution_margin = None if contribution_profit is None or net_sales == 0 else contribution_profit / net_sales

    roas = None if not vals["ad_spend"] else vals["sales"] / vals["ad_spend"]
    aov = None if not vals["orders"] else vals["sales"] / vals["orders"]
    ctr = None if not vals["impressions"] or vals["clicks"] is None else vals["clicks"] / vals["impressions"]
    conversion = None if not vals["visits"] or vals["orders"] is None else vals["orders"] / vals["visits"]

    level1 = vals["sales"] is not None
    level2 = contribution_profit is not None

    return {
        "rows": len(x),
        "mapping": mapping,
        "values": vals,
        "level1_basic_sales": level1,
        "level2_profitability": level2,
        "level3_advanced_finance": False,
        "missing_for_profitability": missing_profit,
        "net_sales": net_sales,
        "contribution_profit": contribution_profit,
        "contribution_margin": contribution_margin,
        "roas": roas,
        "aov": aov,
        "ctr": ctr,
        "conversion": conversion,
    }
