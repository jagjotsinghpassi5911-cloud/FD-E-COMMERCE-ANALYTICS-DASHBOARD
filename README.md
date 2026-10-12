# FD INTELLIGENCE · E-Commerce Analytics Dashboard

**Academic minor project | Jagjot Singh Passi · Roll no. 2446571 · BCA · PCTE Ludhiana**  
**Course instructor:** Ms. Sarbjeet Kaur  
**Official topic:** FD E-Commerce Analytics Dashboard

> **Data disclosure:** Included transactions, customer names, campaigns and campaign performance are **synthetic demonstration data** (realistic examples, but NOT real orders from an FD store). No public dataset can legitimately supply actual private FD-store sales or advertising spend without access to the source. See `docs/REAL_WORLD_DATA_PLAN.md`.

## What you get

- Multi-page interactive **Streamlit** dashboard with dark professional UI, national/city filters, date/category slicers and dynamic charts.
- **MongoDB** primary deployment mode with collection snapshots and a version switch; **SQLite offline demonstration fallback**, useful for faculty laptops.
- Six integrated datasets: customers, orders, order_items, products, marketing_campaigns and campaign_conversions.
- Realized sales KPIs, product, region, payment, weekday, seasonality and margin analyses.
- Customer RFM segmentation, cohort retention, repeat purchase analysis and optional K-Means clustering.
- Attribution-based ROAS, CPA, contribution ROI proxy, channel comparisons and campaign spend allocation.
- Administrator-gated full CSV backup and CSV/Excel import, spreadsheet export, audit trail and data dictionary.
- Repeatable synthetic data generator, quality constraints, automated tests and faculty walkthrough.

## 1. FASTEST START (WINDOWS · offline demo)

1. Install **Python 3.11 or 3.12** from python.org and check **Add python.exe to PATH**.
2. Unzip the project. Double-click `RUN_WINDOWS.bat`.
3. The launcher sets up `.venv`, installs dependencies, creates a database if absent and opens Streamlit at **http://localhost:8501**.
4. To unlock data imports and full backups, open `.env` and set `ADMIN_PASSWORD=your-own-strong-password`, then restart the launcher.
5. The supplied `data/demo/*.csv` contains the exact synthetic seed data for recovery. Do not present this as a genuine FD-store extract.

If the launcher cannot find Python, open PowerShell in the project directory and run:

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python seed.py
python -m streamlit run app.py
```

If PowerShell blocks `Activate.ps1`, **no change to execution policy is required**: invoke `.\.venv\Scripts\python.exe` instead of `python` for the last three commands.

### Mac/Linux

```bash
chmod +x RUN_MAC_LINUX.sh
./RUN_MAC_LINUX.sh
```

## 2. USE REAL MONGODB (primary stack in Phase 1)

### Choice A: MongoDB Community Server on Windows

1. Install MongoDB Community Server and run its local service.
2. Copy `.env.example` to `.env` if it is missing.
3. Change the configuration to:

```env
DATA_BACKEND=mongodb
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=fd_ecommerce_analytics
ADMIN_PASSWORD=choose-your-own-password
```

4. From the project directory:

```powershell
.\.venv\Scripts\python.exe seed.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

5. Connect using MongoDB Compass to database `fd_ecommerce_analytics`. You should see collections for the six datasets plus `fd_metadata` and `fd_audit`.
6. Open **Data Studio** and verify the UI says **MongoDB / persistent**. This is how you demonstrate actual MongoDB integration instead of claiming a SQLite demo uses MongoDB.

### Choice B: MongoDB Atlas

1. Create an Atlas project / database deployment at mongodb.com, following current Atlas requirements for access and pricing.
2. Create a dedicated database user and allow your specific IP in Network Access.
3. Paste the provided connection string with YOUR credentials in your local `.env` (URI-encode special characters in passwords).
4. Change `DATA_BACKEND=mongodb` and run the two commands above.
5. **Never** put `.env` or MongoDB passwords in a public repository or in screenshots.

No MongoDB installed? Stay in SQLite demo mode until the live database demonstration. The project is still functional offline, but clearly label the backend correctly to faculty.

## 3. START CLEAN / GENERATE DIFFERENT DATA

```bash
python seed.py --customers 1250 --orders 5200 --seed 42
python -m pytest tests -q
```

**WARNING:** `seed.py` **replaces the active dataset**. Back up a real imported dataset via Data Studio before running it.

## 4. IMPORT YOUR OWN DATA

1. In sidebar unlock **Administrator access** (requires `ADMIN_PASSWORD` in `.env`).
2. Go to **Data Studio** → **Backup complete database** first.
3. Choose **One Excel workbook** with six correctly named sheets, or six named CSV files.
4. You can download the **blank Excel template** from the UI.
5. Fill required fields exactly as shown. IDs can be alphanumeric and must be consistent between tables.
6. Provide a source description, tick the replacement confirmation, and replace the active dataset.
7. After validation, the dashboard updates immediately; import creates a persistent audit entry.

Imports require **all six tables**; you may provide empty `marketing_campaigns` / `campaign_conversions` if you have no genuine marketing source. Do **not** fabricate conversion attribution just to display strong ROI.

### Core rules

- `order_items.unit_price × quantity` summed by order must equal `orders.total_amount` (tolerance ₹0.02).
- Every order has a customer and at least one item; every item has a valid product.
- Campaign conversions refer to real `Delivered` orders that occurred during their campaign date windows, with **at most one campaign attribution per order**.
- No negative costs/prices/spend, no clicks exceeding impressions, no order predating customer registration.
- `Delivered` = realized revenue; `Shipped`, `Cancelled` and `Returned` are **excluded** from realized revenue.

## 5. RUN THE FACULTY DEMONSTRATION

Show these pages in order:

1. Executive Overview → KPI metrics update with filters.
2. Sales Intelligence → trends, payment mix, downloadable sales file.
3. Customer Intelligence → RFM, cohort matrix, optional K-Means.
4. Campaign & ROI → spend, ROAS, CPA, revenue attribution, limitations.
5. Product Performance → margins, ABC analysis.
6. Data Studio → prove connected database, audit trail, schema validation and CSV/Excel import/backup.
7. Decision Lab → business recommendations and what-if scenario.
8. Faculty Guide → live walkthrough and learning material.

`docs/PROJECT_REPORT.md`, `docs/FACULTY_VIVA_GUIDE.md` and the prepared Word/PDF report explain the architecture, formulas, design diagrams, testing, limitations and likely questions.

## 6. METRIC DEFINITIONS

| KPI | Exact interpretation |
|---|---|
| Revenue | Sum of delivered-order line `quantity × unit_price` |
| Orders | Unique delivered orders containing selected lines |
| AOV | Filtered revenue / unique qualifying delivered orders |
| COGS proxy | Delivered units × `products.unit_cost` (catalog snapshot) |
| ROAS | Single-touch attributed delivered revenue / allocated spend |
| CPA | Allocated spend / attributed delivered order count |
| ROI proxy | (Attributed revenue – catalog COGS – allocated spend) / allocated spend × 100 |
| RFM | Recency (days to end date+1), delivered-order count, delivered-order spend |
| Cohort retention | % of first-purchase customers returning in month +n |

**Important:** Campaign spend and clicks are allocated by time overlap when the dashboard date filter covers part of a campaign. Marketing data remains **national** when regional/product filters are used because no regional or product-wise spend allocation data are available. This system is an **analytical prototype**, not production-grade financial accounting, causal ad incrementality measurement, or a live payment store.

## 7. DIRECTORY MAP

```
FD_Ecommerce_Analytics_Professional/
├── app.py                       # Dashboard and data manager
├── core/
│   ├── schema.py                # Input rules and Excel schema
│   ├── generator.py             # Transparent synthetic generator
│   ├── analytics.py             # Tested formulas and cohorts
│   └── repository.py            # MongoDB or SQLite implementations
├── seed.py                      # Create and commit demo data
├── requirements.txt
├── .env.example                 # Safe configuration template
├── RUN_WINDOWS.bat
├── RUN_MAC_LINUX.sh
├── tests/test_system.py         # Automated proof of functionality
├── data/demo/*.csv             # Repeatable synthetic source tables
├── data/fd_demo.db              # Ready-to-open offline demonstration
├── docs/                       # Viva, report, provenance and architecture
└── .streamlit/config.toml       # Dark professional theme
```

## 8. SECURITY, SCOPE AND LIMITATIONS

- Basic password lock controls **administrative actions only**. It is an educational prototype, **not** secure enterprise RBAC / authentication. Public dashboards still reveal aggregated/limited customer ID information. **Do not deploy real personally identifiable information publicly** without proper authentication, consent, permissions, encrypted storage, and privacy governance.
- Password is read from `.env`; this file is gitignored. Use professional identity providers for real deployment.
- Source attribution for imported data is self-declared, not third-party verified.
- MongoDB loads consistent batches with an active batch identifier. SQLite uses a transaction; both validate the full dataset before switching.
- This is a **manual refresh workflow** after import, not a live connection to Shopify, a payment gateway, or a real-time streaming feed. Live ingestion is a planned extension, **not an existing feature**.
- If no campaign marketing data are available, the correct result is **no attributable campaign metrics**, not invented returns.

## 9. ORIGINAL SYNOPSIS VS IMPLEMENTED STACK

The supplied synopsis states **MERN (MongoDB / Express / React / Node)**; Phase 1 faculty evaluation states **Python / MongoDB / Streamlit**; the supplied old code used **Python / SQLite / Streamlit**. This rebuilt system uses **Python / Streamlit / MongoDB** for the evaluated stack, with a separately labeled SQLite offline mode. Update the original synopsis before resubmission rather than claiming the new dashboard was built in React.

© Academic demonstration · Source files may be adapted for project evaluation.
