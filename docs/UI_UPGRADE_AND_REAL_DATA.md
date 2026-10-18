# FD E-Commerce Analytics Dashboard — Visual Upgrade and Authentic Data Guide

## What this upgrade actually does

- Adds an **Appearance** sidebar control for **System / Light / Dark** using Streamlit session state and theme-sensitive Python/Plotly styling. **System** follows the effective Streamlit/browser theme. These choices are specific to the current browser session, not saved permanently to MongoDB.
- Reworks the oversized five-wide KPI layout into 3+2 cards, and uses **₹ lakh/crore compact formatting** with exact-value tooltips.
- Updates dynamic chart backgrounds, labels, tables, color contrast, hero banners, sidebar spacing and small-screen responsive rules. Replaces deprecated `use_container_width` with `width="stretch"`.
- Hides **Administrator workspace** entirely if `ADMIN_PASSWORD` is unset; leaves the password-gated import controls for the trusted local admin session. This is NOT a substitute for production-grade authentication; database reader credentials enforce read-only remote access.
- Restricts individual customer/order previews and sensitive CSVs to admin sessions, leaving non-admin users aggregated insights.
- Fixes the misleading provenance treatment of `copied_from_local:synthetic_demo(seed=42)`. Copied synthetic data remain **simulated**, even after MongoDB Atlas migration.
- Adds **Real Data Explorer**, a read-only sandbox for the *authentic* UCI Online Retail (2010–2011) transactions. It analyzes in **GBP**, labels them historical, and does not replace your project's MongoDB database. Imports only into the current Streamlit viewer's session.
- Adds a **Refresh current database snapshot** button. This reloads currently stored MongoDB data; it is not itself live store synchronization.

## Critical distinction: authentic vs current vs live

| Data source | Real records? | Real-time? | FD-store data? | Marketing ROI available? |
|---|---|---|---|---|
| `synthetic_demo(seed=42)` in MongoDB | No | No | Fictional illustration | Simulated proxy only |
| UCI Online Retail downloaded from official source | Yes (historical transactions) | No (2010–2011) | No (UK gift business) | No |
| Authorized store orders (Shopify/WooCommerce/POS) | Yes, once connected | Can be near-real-time with authorized sync | Only when from FD store | Only with genuine ad cost + attribution data |

**Never call simulated records genuine revenue.** No authenticated operational shop source has been supplied, so an automatic real-time FD-store feed cannot responsibly be implemented yet.

## How to show real historical records to faculty without falsifying provenance

1. Download *Online Retail.xlsx* from the [UCI Online Retail repository](https://archive.ics.uci.edu/dataset/352/online+retail). The dataset covers real UK gift retailer transactions in 2010–2011, and is **not** an FD fashion store dataset. The dataset license is CC BY 4.0.
2. Open your upgraded Streamlit app and select **Real Data Explorer**.
3. Upload `.xlsx` (or an equivalent CSV with the UCI headings). Do not upload sensitive unrelated client data to an untrusted public session.
4. Review historical GBP sales, invoice counts, cancellation counts, product performance and country mix.
5. Cite: Chen, D., *Online Retail*, UCI Machine Learning Repository, https://doi.org/10.24432/C5BW33 (confirm dataset citation from its source page).
6. Explain to faculty that this **historical dataset is studied separately**, while the FD demonstration dashboard still uses the clearly labeled simulated dataset.

No marketing campaigns, costs, customer signup dates, inventory or payment methods are fabricated in Real Data Explorer. Cancellation/negative-quantity invoices are excluded from realized sales.

## What actually produces real-time FD store data

You need **owner-authorized access** to an operating store. Examples:

- Shopify: Admin GraphQL API, `read_orders` (older than 60 days requires additional permission), plus product data. Secure server-side app token and a service that periodically syncs to Atlas. See [Shopify orders API](https://shopify.dev/docs/api/admin-graphql/latest/queries/orders).
- WooCommerce: REST APIs with owner-provided access; limit permissions and secure credentials server-side.
- Physical store: POS sales exports at agreed intervals.
- Advertising ROI: matching dated real campaign spend, clicks and attribution records from Google Ads/Meta/e-commerce platform, explicitly defining attribution and data limitations.

**Do not put live API keys or customer-identifying exports in GitHub.** Before importing operational customer records, implement proper authentication/authorization and privacy controls; a simple sidebar admin password is not production-grade security.

## Exact upgrade procedure for Windows + GitHub + Streamlit Cloud

1. **Back up** your deployed project folder (and GitHub state) first. Do not modify `.env`, MongoDB databases or rerun `seed.py`/migration.
2. Extract `FD_UI_Upgrade_Patch.zip` to a temporary folder. Copy the extracted `app.py`, `requirements.txt`, `.streamlit/config.toml`, `core/appearance.py`, `core/real_data.py` and `tests/test_real_data_and_theme.py` into the corresponding paths of your **existing** VS Code project. Keep the current `core/repository.py` and all your data untouched.
3. Terminal from your VS Code project root (CMD):

    ```bat
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    .venv\Scripts\python.exe -m py_compile app.py
    .venv\Scripts\python.exe -m pytest tests -q
    .venv\Scripts\python.exe -m streamlit run app.py
    ```

4. Open localhost:8501. Test Appearance options, charts, Data Studio, visibility of admin, and historical file upload.
5. Inspect staged file list **before uploading**:

    ```bat
    git add app.py requirements.txt .streamlit/config.toml core/appearance.py core/real_data.py tests/test_real_data_and_theme.py
    git diff --cached --name-only
    git commit -m "Upgrade dashboard themes and real-data explorer"
    git push origin main
    ```

6. Verify Streamlit automatically redeploys and uses the existing Atlas secrets. Keep `ADMIN_PASSWORD` **unset in Streamlit cloud Secrets**, leaving the cloud copy read-only.

## Local vs hosted admin controls

The local view showed **Administrator access** because you configured `ADMIN_PASSWORD` in your local `.env`. The prior cloud view showed the control even when no password was set because the original app rendered the expander unconditionally. The patch fixes that cosmetic issue and restricts raw exports. It does **not** grant/alter MongoDB permissions. For production-grade real customer data, build an authenticated role-based application before publishing.

## Limitations and testing

We ran Python syntax compilation and the project/unit tests on the supplied project snapshot. A live Streamlit browser session and your cloud MongoDB Atlas secrets were not accessible to us in the build environment. Test the finished deployment yourself; the current local/online app may have edits not included in the previously supplied project ZIP. Preserve your current files and review diffs before replacing `app.py`.
