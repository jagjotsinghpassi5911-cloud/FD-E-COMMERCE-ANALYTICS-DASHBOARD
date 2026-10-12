# Real-World Data Acquisition and Provenance Plan

## Non-negotiable principle

No legitimate source in the uploads contains verified FD-store transactions, private purchase behavior, advertising expenditure or CRM conversion attribution. The old `generate_data.py` used Faker/random generation; the rebuilt demo uses transparent reproducible synthetic generation. Realism is not authenticity. **Never claim simulated sales are real.**

## What IS in the supplied materials

- Old demo: fashion and decor catalog, simulated Indian customer names/regions, transactions, campaigns and generated conversion links.
- Official topic: FD E-Commerce Analytics Dashboard, sales/customer/marketing ROI and strategic decisions.
- Faculty Phase 1 note: train on dynamic/real-time data; complete DB integration; show full demo.
- No signed data access agreement, transactional export from a genuine store, or raw advertisement-manager export is supplied.

## Recommended primary route: consented store exports

1. Contact an FD student-run boutique, local small e-commerce seller, Shopify/WooCommerce store or college-design merchandise store with permission from owner/instructor.
2. Request order CSV for an explicitly agreed historical range, line items, catalog SKU names, and anonymized customer IDs/regions. Never take customer phone numbers, home addresses or emails without necessity and lawful authority.
3. For marketing ROAS, request campaign IDs, real platform spend, clicks and impressions from Google Ads/Meta Ads, and **documented order-to-campaign attribution** from analytics/UTM conversion logs.
4. Capture provenance: source organization, export UTC time, reporting period, contact permission, field meanings, currency, missing values, returns policy, attribution model, identity masking and any material transformations.
5. Map data into the exact six-table schema using the workbook template. Leave unsupported fields or campaign tables blank rather than inventing spend or marketing conversions.
6. Reconcile accounting totals and validate with a few source invoices before importing. Avoid sharing identifiable transaction logs on public hosting.
7. Label metrics as **real-world business records supplied by [authorized source]** only after confirming them.

## Optional third-party public dataset for historical sales exercises

**UCI Machine Learning Repository — Online Retail:** documented historical transactions from a UK-based non-store retailer, Dec 2010–Dec 2011. This is **real transactional research data**, but **not an FD fashion store** and **not an India 2026 dataset**. It does not include authenticated advertising spend or campaign-to-order attribution, so full marketing ROI cannot legitimately be computed from it.

Source: https://archive.ics.uci.edu/dataset/352/online+retail

**Google Analytics — obfuscated ecommerce BigQuery demo:** example event export from Google Merchandise Store with redacted/obfuscated fields and internal limitations. It is **not** a verified source of FD-store sales or campaign profitability, and reconstructing the complete six-table schema requires nontrivial mapping.

Source: https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset

The project intentionally does not silently download, alter, or claim ownership over these sources. A human must evaluate licensing, completeness, time period, field mapping and privacy before importing.

## How to defend your current data in front of faculty

> "The software is a working analytics proof of concept. The included dataset is explicitly synthetic but has realistic product prices, seasonal demand, statuses and referentially consistent campaign attribution. It can be replaced with validated real exports through Excel/CSV, and the MongoDB backend stores each dataset persistently. I will not claim invented revenue is measured business performance."

## Real-time clarification

A MongoDB database **is not the same thing** as a real-time feed. This project can save imported data immediately and recalculate the dashboard dynamically. **Actual live sales ingestion** requires a documented API/webhook and permissions, retry and authentication logic. Show the faculty dynamic refresh through a new import and updated KPIs; do not call it a real-time Shopify integration until such a connection exists.
