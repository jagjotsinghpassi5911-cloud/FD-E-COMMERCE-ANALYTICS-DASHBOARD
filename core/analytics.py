"""Reusable, tested business-metric definitions. Monetary values in INR."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

REALIZED = "Delivered"  # Shipped = pending, Cancelled / Returned = not realized.

def order_scope(data, start=None, end=None, region="All", only_delivered=True):
    o = data["orders"].copy()
    o["order_date"] = pd.to_datetime(o.order_date)
    if only_delivered:
        o = o[o.status.eq(REALIZED)]
    if start is not None:
        o = o[o.order_date >= pd.Timestamp(start)]
    if end is not None:
        o = o[o.order_date <= pd.Timestamp(end)]
    if region != "All":
        eligible = data["customers"].loc[data["customers"].region.eq(region), "customer_id"]
        o = o[o.customer_id.isin(eligible)]
    return o

def sales_lines(data, start=None, end=None, region="All", category="All"):
    """One row per order line; applying category filters here prevents double-counting."""
    o = order_scope(data,start,end,region)
    lines = data["order_items"].merge(o[["order_id","customer_id","order_date","payment_method"]],on="order_id",how="inner")
    prod = data["products"][["product_id","name","category","unit_cost"]]
    lines = lines.merge(prod,on="product_id",how="left",validate="many_to_one")
    if category != "All":
        lines = lines[lines.category.eq(category)]
    lines = lines.copy()
    lines["revenue"] = lines.quantity * lines.unit_price
    lines["cogs"] = lines.quantity * lines.unit_cost
    lines["contribution"] = lines.revenue - lines.cogs
    return lines

def sales_kpis(lines):
    revenue=float(lines.revenue.sum()) if len(lines) else 0.
    orders=int(lines.order_id.nunique()) if len(lines) else 0
    return {"revenue":revenue,"orders":orders,"aov":revenue/orders if orders else 0.,
            "customers":int(lines.customer_id.nunique()) if len(lines) else 0,
            "units":int(lines.quantity.sum()) if len(lines) else 0,
            "contribution":float(lines.contribution.sum()) if len(lines) else 0.}

def rfm_segments(data, as_of=None, region="All"):
    """Lifetime delivered orders up to 'as_of'; not restricted to chart start date."""
    if as_of is None:
        as_of = pd.Timestamp(data["orders"].order_date.max())
    o=order_scope(data,end=as_of,region=region)
    if o.empty:
        return pd.DataFrame(columns=["customer_id","recency","frequency","monetary","r_score","f_score","m_score","segment"])
    ref = pd.Timestamp(as_of) + pd.Timedelta(days=1)
    r=o.groupby("customer_id").agg(last_order=("order_date","max"), frequency=("order_id","nunique"),monetary=("total_amount","sum")).reset_index()
    r["recency"]=(ref-r.last_order).dt.days
    for col,key,ascending in [("recency","r_score",False),("frequency","f_score",True),("monetary","m_score",True)]:
        r[key]=np.ceil(r[col].rank(method="average",ascending=ascending,pct=True)*5).astype(int).clip(1,5)
    def classify(v):
        if v.r_score>=4 and v.f_score>=4 and v.m_score>=4: return "Champions"
        if v.f_score>=4 and v.r_score>=3: return "Loyal"
        if v.r_score<=2 and v.f_score>=3: return "At risk"
        if v.r_score<=2: return "Dormant"
        if v.frequency==1: return "One-time"
        return "Growing"
    r["segment"]=r.apply(classify,axis=1)
    return r.drop(columns="last_order")

def cohort_retention(data):
    """Each month shows fraction of acquired customers placing an order in month + n."""
    o=order_scope(data)
    if o.empty: return pd.DataFrame()
    o["month"]=o.order_date.dt.to_period("M")
    first=o.groupby("customer_id").month.min().rename("cohort")
    o=o.join(first,on="customer_id")
    o["month_number"]=(o.month.dt.year-o.cohort.dt.year)*12+(o.month.dt.month-o.cohort.dt.month)
    n=o.groupby(["cohort","month_number"]).customer_id.nunique().unstack(fill_value=0)
    base=n[0]
    res=n.div(base,axis=0).mul(100).round(1)
    res.index=res.index.astype(str)
    return res

def marketing_performance(data,start=None,end=None):
    """Single-touch attributed revenue, contribution proxy and prorated campaign spend.

    Region/category filters are intentionally NOT applied to national marketing spend.
    Impression/click allocations are estimates for partial campaign periods.
    """
    camps=data["marketing_campaigns"].copy()
    camps["start_date"]=pd.to_datetime(camps.start_date)
    camps["end_date"]=pd.to_datetime(camps.end_date)
    start=pd.Timestamp(start) if start else camps.start_date.min()
    end=pd.Timestamp(end) if end else camps.end_date.max()
    days=(camps.end_date-camps.start_date).dt.days+1
    overlap_start=camps.start_date.where(camps.start_date>=start,start)
    overlap_end=camps.end_date.where(camps.end_date<=end,end)
    overlap=(overlap_end-overlap_start).dt.days.add(1).clip(lower=0)
    fraction=overlap/days
    camps["allocated_spend"]=(camps.spend*fraction).round(2)
    camps["estimated_impressions"]=(camps.impressions*fraction).round().astype(int)
    camps["estimated_clicks"]=(camps.clicks*fraction).round().astype(int)
    valid=order_scope(data,start,end)
    a=data["campaign_conversions"].merge(valid[["order_id","customer_id","total_amount"]],on=["order_id","customer_id"],how="inner")
    lines=sales_lines(data,start,end)
    cogs=lines.groupby("order_id").cogs.sum().rename("cogs")
    a=a.join(cogs,on="order_id")
    a["contribution"] = a.total_amount-a.cogs
    agg=a.groupby("campaign_id").agg(conversions=("order_id","nunique"),attributed_revenue=("total_amount","sum"),attributed_contribution=("contribution","sum"))
    camps=camps.join(agg,on="campaign_id").fillna({"conversions":0,"attributed_revenue":0,"attributed_contribution":0})
    camps["conversions"]=camps.conversions.astype(int)
    camps["roas"]=np.where(camps.allocated_spend>0,camps.attributed_revenue/camps.allocated_spend,np.nan)
    camps["roi_proxy_pct"]=np.where(camps.allocated_spend>0,(camps.attributed_contribution-camps.allocated_spend)/camps.allocated_spend*100,np.nan)
    camps["cpa"]=np.where(camps.conversions>0,camps.allocated_spend/camps.conversions,np.nan)
    camps["ctr_pct"]=np.where(camps.estimated_impressions>0,camps.estimated_clicks/camps.estimated_impressions*100,np.nan)
    camps["cvr_pct"]=np.where(camps.estimated_clicks>0,camps.conversions/camps.estimated_clicks*100,np.nan)
    return camps

def channel_performance(camps):
    if camps.empty: return pd.DataFrame()
    group=camps.groupby("channel",as_index=False).agg(spend=("allocated_spend","sum"),revenue=("attributed_revenue","sum"),
        contribution=("attributed_contribution","sum"),conversions=("conversions","sum"), clicks=("estimated_clicks","sum"),impressions=("estimated_impressions","sum"))
    group["roas"]=np.where(group.spend>0,group.revenue/group.spend,np.nan)
    group["roi_proxy_pct"]=np.where(group.spend>0,(group.contribution-group.spend)/group.spend*100,np.nan)
    group["cpa"]=np.where(group.conversions>0,group.spend/group.conversions,np.nan)
    return group

def quality_snapshot(data):
    o=data["orders"]
    a=data["campaign_conversions"]
    delivered=o[o.status.eq("Delivered")]
    return {"products":len(data["products"]),"customers":len(data["customers"]),"orders":len(o),
            "delivered":len(delivered),"cancelled":int(o.status.eq("Cancelled").sum()),
            "returned":int(o.status.eq("Returned").sum()),"campaigns":len(data["marketing_campaigns"]),
            "attributed_orders":len(a),"attributed_share_pct":round(100*len(a)/len(delivered),1) if len(delivered) else 0}

def recommendations(data,lines,camps,segments):
    recs=[]
    if not lines.empty:
        cat=lines.groupby("category").revenue.sum().sort_values(ascending=False)
        recs.append(("Category investment",f"{cat.index[0]} leads the selected sales scope at ₹{cat.iloc[0]:,.0f}. Check margins and stock availability before expanding spend."))
        payment=lines.drop_duplicates("order_id").payment_method.value_counts()
        if not payment.empty:
            recs.append(("Checkout experience",f"{payment.index[0]} is the most-used payment method among delivered orders in scope ({payment.iloc[0]:,} orders)."))
    if not segments.empty:
        dormant=int(segments.segment.isin(["At risk","Dormant"]).sum())
        recs.append(("Retention",f"{dormant:,} past customers are in at-risk or dormant segments as of the selected end date. Consider a targeted win-back test."))
    cs=channel_performance(camps)
    active=cs[cs.spend>0].sort_values("roas",ascending=False)
    if not active.empty:
        top=active.iloc[0]
        recs.append(("Campaign allocation",f"{top.channel} has the highest observed attributed ROAS ({top.roas:.2f}×). Verify attribution assumptions before changing budgets."))
    return recs
