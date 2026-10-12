"""Reproducible, India-themed SYNTHETIC commerce data. Never represent as real sales."""
from __future__ import annotations
from datetime import date, timedelta
import numpy as np
import pandas as pd
from faker import Faker
from .schema import validate

CATALOG = [
 ("Linen Kurta Set", "Fashion", 1499), ("Ajrakh Cotton Saree", "Fashion", 2199),
 ("Printed Co-ord Set", "Fashion", 1899), ("Festive Anarkali", "Fashion", 3499),
 ("Handloom Dupatta", "Fashion", 899), ("Denim Overshirt", "Fashion", 1699),
 ("Chikankari Kurti", "Fashion", 1799), ("Organic Cotton Tee", "Fashion", 799),
 ("Palazzo Pants", "Fashion", 1099), ("Indigo Shirt Dress", "Fashion", 2399),
 ("Nehru Jacket", "Fashion", 2499), ("Silk Stole", "Fashion", 1299),
 ("Embroidered Juttis", "Accessories", 1299), ("Oxidised Earrings", "Accessories", 599),
 ("Leatherette Tote", "Accessories", 1999), ("Ethnic Clutch", "Accessories", 899),
 ("Canvas Sling Bag", "Accessories", 1199), ("Beaded Bracelet", "Accessories", 449),
 ("Block Print Scarf", "Accessories", 799), ("Pearl Hair Clip Set", "Accessories", 399),
 ("Scrunchie Trio", "Accessories", 349), ("Minimalist Belt", "Accessories", 749),
 ("Rattan Storage Basket", "Home Decor", 1199), ("Terracotta Planter Duo", "Home Decor", 899),
 ("Macrame Wall Hanging", "Home Decor", 1799), ("Aroma Candle Gift Set", "Home Decor", 1099),
 ("Ceramic Vase Pair", "Home Decor", 1899), ("Jute Table Runner", "Home Decor", 649),
 ("Handwoven Cushion Cover", "Home Decor", 799), ("Brass Tea Light Holder", "Home Decor", 1399),
 ("Bamboo Serving Tray", "Home Decor", 1499), ("Printed Wall Art", "Home Decor", 999),
]
REGIONS = ["Delhi NCR", "Mumbai", "Bengaluru", "Punjab", "Pune", "Hyderabad", "Chennai", "Kolkata", "Jaipur", "Ahmedabad"]
REGION_PROB = [.20, .16, .15, .12, .10, .09, .07, .05, .04, .02]
CHANNELS = ["Google Ads", "Instagram", "Email", "Influencer", "Meta Ads", "Organic Social"]

def generate(seed: int=42, n_customers: int=1250, n_orders: int=5200,
             start: str="2025-01-01", end: str="2026-09-30") -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    Faker.seed(seed)
    fake = Faker("en_IN")
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if not 30 <= (last-first).days <= 2000 or n_customers < 10 or n_orders < 10:
        raise ValueError("Please provide a 30–2000 day period and at least 10 customers/orders")
    products = []
    for i, (name, cat, price) in enumerate(CATALOG, 1):
        cost = round(price * float(rng.uniform(.43,.73)), 2)
        products.append((str(i), name, cat, price, cost, int(rng.integers(12, 185))))
    products = pd.DataFrame(products, columns=["product_id","name","category","unit_price","unit_cost","stock"])
    customers=[]
    for i in range(1,n_customers+1):
        # Sign-ups happen before or during the reporting window.
        offset = int(rng.integers(-240, (last-first).days+1))
        signup = first + timedelta(days=offset)
        customers.append((str(i), fake.name(), signup.isoformat(), str(rng.choice(REGIONS,p=REGION_PROB))))
    customers = pd.DataFrame(customers,columns=["customer_id","name","signup_date","region"])
    # Favors festive season and weekends. All patterns are ASSUMPTIONS, not measured facts.
    dates = pd.date_range(first,last)
    month_multipliers={1:.82,2:.79,3:.91,4:.84,5:.82,6:.87,7:.95,8:1.02,9:1.18,10:1.60,11:1.55,12:1.29}
    weights = np.array([month_multipliers[d.month] * (1.16 if d.weekday()>=5 else 1) for d in dates],float)
    weights /= weights.sum()
    order_dates = rng.choice(dates, n_orders, replace=True, p=weights)
    order_dates.sort()
    signup_dt = pd.to_datetime(customers.signup_date).to_numpy(dtype='datetime64[ns]')
    customer_ids = customers.customer_id.to_numpy()
    # Customers who have ordered before are somewhat likelier to return.
    loyalty_weight = rng.lognormal(mean=0.0, sigma=0.85, size=n_customers)
    orders=[]; items=[]
    for index, dt in enumerate(order_dates, 1):
        eligible = signup_dt <= np.datetime64(dt)
        p = loyalty_weight * eligible
        p=p/p.sum()
        cid = str(rng.choice(customer_ids,p=p))
        item_count = int(rng.choice([1,2,3],p=[.58,.30,.12]))
        chosen = rng.choice(len(products),size=item_count,replace=False)
        total = 0.0
        for j, idx in enumerate(chosen,1):
            prod = products.iloc[int(idx)]
            qty = int(rng.choice([1,2,3],p=[.84,.14,.02]))
            price = float(prod.unit_price)
            items.append((str(index)+'-'+str(j),str(index),str(prod.product_id),qty,price))
            total += qty*price
        status = str(rng.choice(["Delivered","Shipped","Cancelled","Returned"],p=[.84,.07,.06,.03]))
        payment = str(rng.choice(["UPI","Card","Cash on Delivery","Net Banking"],p=[.48,.29,.17,.06]))
        orders.append((str(index),cid,pd.Timestamp(dt).strftime('%Y-%m-%d'),status,payment,round(total,2)))
    orders = pd.DataFrame(orders,columns=["order_id","customer_id","order_date","status","payment_method","total_amount"])
    items = pd.DataFrame(items,columns=["item_id","order_id","product_id","quantity","unit_price"])
    # Campaigns are distributed over time with non-overlapping bounds only where appropriate.
    campaigns=[]
    n_campaigns=14
    span=(last-first).days
    for i in range(n_campaigns):
        campaign_start=first+timedelta(days=int(i*max(0,span-45)/(n_campaigns-1)))
        campaign_end=min(last,campaign_start+timedelta(days=int(rng.integers(22,52))))
        channel=CHANNELS[i%len(CHANNELS)]
        spend=round(float(rng.integers(17000,82000)),2)
        impressions=int(rng.integers(38000,240000))
        clicks=int(rng.integers(1800, min(15000,impressions//3)))
        campaigns.append((str(i+1), f"{campaign_start:%b %Y} • {channel} Collection",channel,campaign_start.isoformat(),campaign_end.isoformat(),spend,impressions,clicks))
    campaigns = pd.DataFrame(campaigns,columns=["campaign_id","name","channel","start_date","end_date","spend","impressions","clicks"])
    attribution=[]; selected_orders=set()
    for _, c in campaigns.iterrows():
        eligible = orders[(orders.order_date>=c.start_date)&(orders.order_date<=c.end_date)&(orders.status=='Delivered')]
        eligible = eligible[~eligible.order_id.isin(selected_orders)]
        max_conv=min(len(eligible),int(c.clicks),int(rng.integers(46,112)))
        if max_conv:
            selected = rng.choice(eligible.index.to_numpy(),size=max_conv,replace=False)
            for oi in selected:
                row=orders.loc[oi]
                attribution.append((str(len(attribution)+1),str(c.campaign_id),str(row.order_id),str(row.customer_id)))
                selected_orders.add(str(row.order_id))
    attr = pd.DataFrame(attribution,columns=["attribution_id","campaign_id","order_id","customer_id"])
    return validate(dict(zip(["products","customers","orders","order_items","marketing_campaigns","campaign_conversions"],
                             [products,customers,orders,items,campaigns,attr])))
