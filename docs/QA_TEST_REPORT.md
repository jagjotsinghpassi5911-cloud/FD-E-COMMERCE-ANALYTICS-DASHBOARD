# Data quality / reproducibility evidence

**Data provenance:** `synthetic_demo(seed=42)` — synthetically generated; not genuine company data.

**Generator:** `python seed.py --seed 42 --customers 1250 --orders 5200`

**Row counts:** products=32, customers=1,250, orders=5,200, order_items=8,037, marketing_campaigns=14, campaign_conversions=1,009

**Status mix:** Delivered=4,399, Shipped=351, Cancelled=301, Returned=149

**Realized sales:** ₹10,750,033.00 across 4,399 delivered orders and 891 unique buyers.

**Campaign totals:** allocated marketing spend ₹638,527.00; single-touch attributed delivered revenue ₹2,525,382.00; ROAS 3.96×. All are simulated performance values, not verified financial results.

**Validation:** six data tables passed schema, date, foreign-key, status, attribution and order-total checks.

**Tests:** 10 of 10 passed via `python -m pytest tests -q`. Includes negative-input rejection and SQLite persistence.

**Execution limitation:** The Streamlit GUI and live MongoDB connection were not runtime-tested in the package preparation environment because the needed Streamlit/PyMongo packages could not be downloaded. Run the Windows launcher and MongoDB instructions on a machine with package access before the faculty demonstration.

**Next verified step:** On Windows, run `RUN_WINDOWS.bat`, test all eight pages, set `ADMIN_PASSWORD`, perform CSV/Excel import/export, then turn on MongoDB and verify persisted collections in MongoDB Compass.
