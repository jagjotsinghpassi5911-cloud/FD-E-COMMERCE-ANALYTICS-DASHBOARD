"""Read-only analytics for a documented authentic UCI historical retail dataset.

Data are never imported into FD MongoDB, currency is GBP, and no campaign
attribution or profit is fabricated. Streamlit uploader holds the file only in
current app session. Source: UCI Online Retail, dataset 352 (CC BY 4.0).
"""
from __future__ import annotations
import pandas as pd

REQUIRED = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "Country"}
MAX_LINES = 750_000
SOURCE_URL = "https://archive.ics.uci.edu/dataset/352/online+retail"


def clean_uci_online_retail(raw: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(raw, pd.DataFrame):
        raise ValueError("Upload a CSV or Excel table.")
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError("Missing UCI Online Retail columns: " + ", ".join(sorted(missing)))
    if len(raw) > MAX_LINES:
        raise ValueError(f"For this demo, upload at most {MAX_LINES:,} invoice lines.")
    cols = list(REQUIRED) + (["CustomerID"] if "CustomerID" in raw.columns else [])
    df = raw[cols].copy()
    df["InvoiceNo"] = df["InvoiceNo"].astype("string").str.strip()
    df["StockCode"] = df["StockCode"].astype("string").str.strip()
    df["Description"] = df["Description"].astype("string").str.strip()
    df["Country"] = df["Country"].astype("string").str.strip()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df = df.dropna(subset=["InvoiceNo", "StockCode", "InvoiceDate", "Quantity", "UnitPrice", "Country"])
    df = df.loc[(df["InvoiceNo"] != "") & (df["Country"] != "")].copy()
    df["is_cancelled"] = df["InvoiceNo"].str.upper().str.startswith("C") | (df["Quantity"] < 0)
    # Only positive valid sales are realized revenue. 0-price gifts stay at £0.
    df["revenue_gbp"] = (df["Quantity"].clip(lower=0) * df["UnitPrice"].clip(lower=0)).where(
        ~df["is_cancelled"] & (df["UnitPrice"] >= 0), 0.0
    )
    return df.reset_index(drop=True)


def summarize_uci_online_retail(clean: pd.DataFrame) -> dict:
    realized = clean.loc[(~clean.is_cancelled) & (clean.Quantity > 0) & (clean.UnitPrice >= 0)]
    monthly = realized.assign(month=realized.InvoiceDate.dt.to_period("M").astype(str)).groupby("month", as_index=False).revenue_gbp.sum()
    products = realized.groupby("Description", as_index=False).agg(revenue_gbp=("revenue_gbp", "sum"), units=("Quantity", "sum")).nlargest(12, "revenue_gbp")
    countries = realized.groupby("Country", as_index=False).revenue_gbp.sum().nlargest(12, "revenue_gbp")
    customers = realized["CustomerID"].dropna().nunique() if "CustomerID" in realized.columns else None
    return {"revenue": float(realized.revenue_gbp.sum()), "invoices": int(realized.InvoiceNo.nunique()),
            "customers": None if customers is None else int(customers), "cancelled_lines": int(clean.is_cancelled.sum()),
            "monthly": monthly, "products": products, "countries": countries}
