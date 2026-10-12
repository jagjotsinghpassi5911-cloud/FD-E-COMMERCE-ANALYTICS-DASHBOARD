"""Canonical tabular schema for FD e-commerce analytics."""
from __future__ import annotations
from io import BytesIO
import pandas as pd

TABLES = {
    "products": ["product_id", "name", "category", "unit_price", "unit_cost", "stock"],
    "customers": ["customer_id", "name", "signup_date", "region"],
    "orders": ["order_id", "customer_id", "order_date", "status", "payment_method", "total_amount"],
    "order_items": ["item_id", "order_id", "product_id", "quantity", "unit_price"],
    "marketing_campaigns": ["campaign_id", "name", "channel", "start_date", "end_date", "spend", "impressions", "clicks"],
    "campaign_conversions": ["attribution_id", "campaign_id", "order_id", "customer_id"],
}
IDS = {
    "products": "product_id", "customers": "customer_id", "orders": "order_id",
    "order_items": "item_id", "marketing_campaigns": "campaign_id", "campaign_conversions": "attribution_id"
}
DATE_COLUMNS = {"customers": ["signup_date"], "orders": ["order_date"], "marketing_campaigns": ["start_date", "end_date"]}
NUMERIC_COLUMNS = {
    "products": ["unit_price", "unit_cost", "stock"],
    "orders": ["total_amount"], "order_items": ["quantity", "unit_price"],
    "marketing_campaigns": ["spend", "impressions", "clicks"],
}
INTEGER_COLUMNS = {"products": ["stock"], "order_items": ["quantity"], "marketing_campaigns": ["impressions", "clicks"]}
ALLOWED_STATUS = {"Delivered", "Shipped", "Cancelled", "Returned"}
MAX_ROWS_PER_TABLE = 100_000

def normalize(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    if set(raw) != set(TABLES):
        raise ValueError(f"Expected exactly these six tables: {', '.join(TABLES)}")
    result = {}
    for name, df in raw.items():
        if name in ("products", "customers", "orders", "order_items") and df.empty:
            raise ValueError(f"{name}: this required table cannot be empty")
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"{name}: not a table")
        absent = [c for c in TABLES[name] if c not in df.columns]
        if absent:
            raise ValueError(f"{name}: missing columns {absent}")
        if len(df) > MAX_ROWS_PER_TABLE:
            raise ValueError(f"{name}: maximum {MAX_ROWS_PER_TABLE:,} records per table in this educational build")
        d = df[TABLES[name]].copy()
        for c in TABLES[name]:
            if d[c].isna().any():
                raise ValueError(f"{name}.{c}: missing values not allowed")
        for c in DATE_COLUMNS.get(name, []):
            dt = pd.to_datetime(d[c], errors="coerce")
            if dt.isna().any():
                raise ValueError(f"{name}.{c}: invalid dates")
            d[c] = dt.dt.strftime("%Y-%m-%d")
        for c in NUMERIC_COLUMNS.get(name, []):
            d[c] = pd.to_numeric(d[c], errors="coerce")
            if d[c].isna().any() or not pd.Series(d[c]).map(lambda x: float('-inf') < x < float('inf')).all():
                raise ValueError(f"{name}.{c}: invalid numeric values")
        for c in INTEGER_COLUMNS.get(name, []):
            if (d[c] % 1 != 0).any():
                raise ValueError(f"{name}.{c}: integers required")
            d[c] = d[c].astype(int)
        for c in [x for x in d.columns if x not in NUMERIC_COLUMNS.get(name, [])]:
            d[c] = d[c].astype(str).str.strip()
            if (d[c] == "").any():
                raise ValueError(f"{name}.{c}: blank values not allowed")
        if d[IDS[name]].duplicated().any():
            raise ValueError(f"{name}: duplicate {IDS[name]} values")
        result[name] = d.reset_index(drop=True)
    return result

def validate(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Validate critical accounting, attribution, and referential integrity rules."""
    d = normalize(raw)
    p, c, o, items, m, a = (d[t] for t in TABLES)
    if not set(o.customer_id).issubset(set(c.customer_id)):
        raise ValueError("orders: unknown customer_id")
    if not set(items.order_id).issubset(set(o.order_id)) or not set(items.product_id).issubset(set(p.product_id)):
        raise ValueError("order_items: unknown order_id or product_id")
    if set(o.order_id) != set(items.order_id):
        raise ValueError("Every order must contain at least one order item")
    if not set(a.order_id).issubset(set(o.order_id)) or not set(a.campaign_id).issubset(set(m.campaign_id)):
        raise ValueError("campaign_conversions: unknown order_id or campaign_id")
    if len(a) and a.order_id.duplicated().any():
        raise ValueError("An order can have at most one campaign attribution (single-touch model)")
    if not set(o.status).issubset(ALLOWED_STATUS):
        raise ValueError(f"orders.status must be in {sorted(ALLOWED_STATUS)}")
    for name, fields in (("products", ["unit_price", "unit_cost", "stock"]),
                         ("orders", ["total_amount"]), ("order_items", ["quantity", "unit_price"]),
                         ("marketing_campaigns", ["spend", "impressions", "clicks"])):
        for f in fields:
            if (d[name][f] < 0).any():
                raise ValueError(f"{name}.{f}: negative values not allowed")
    if (items.quantity < 1).any():
        raise ValueError("Order line quantity must be positive")
    if (m.clicks > m.impressions).any():
        raise ValueError("Campaign clicks cannot exceed impressions")
    if (pd.to_datetime(m.start_date) > pd.to_datetime(m.end_date)).any():
        raise ValueError("Campaign end_date must be on/after start_date")
    totals = items.assign(subtotal=items.quantity * items.unit_price).groupby("order_id").subtotal.sum()
    checks = o.set_index("order_id").total_amount
    if ((totals - checks).abs() > 0.02).any():
        raise ValueError("orders.total_amount does not equal sum(quantity × unit_price) for its items")
    order_dates = o.set_index("order_id")
    signup = c.set_index("customer_id").signup_date
    if (pd.to_datetime(o.order_date).to_numpy() < pd.to_datetime(o.customer_id.map(signup)).to_numpy()).any():
        raise ValueError("Order date cannot be before customer signup")
    if len(a):
        attr = a.merge(o[["order_id", "customer_id", "order_date", "status"]], on="order_id", how="left", suffixes=("_attributed", "_order"))
        if (attr.customer_id_attributed != attr.customer_id_order).any():
            raise ValueError("Campaign attribution customer_id does not match order")
        if (~attr.status.eq("Delivered")).any():
            raise ValueError("Only delivered orders may receive marketing attribution")
        attr = attr.merge(m[["campaign_id", "start_date", "end_date"]], on="campaign_id")
        if ((attr.order_date < attr.start_date) | (attr.order_date > attr.end_date)).any():
            raise ValueError("Attribution must fall within the associated campaign date window")
    return d

def excel_template() -> bytes:
    """One multi-sheet workbook with optional GUIDE, no real transaction data."""
    styled = __import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "demo" / "FD_import_template.xlsx"
    if styled.is_file():
        return styled.read_bytes()
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine="xlsxwriter") as writer:
        for name, columns in TABLES.items():
            pd.DataFrame(columns=columns).to_excel(writer, sheet_name=name, index=False)
    return buff.getvalue()
