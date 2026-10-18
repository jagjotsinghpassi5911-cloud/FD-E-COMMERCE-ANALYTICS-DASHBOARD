"""FD E-Commerce Analytics Dashboard — professional educational analytics demonstration."""
from __future__ import annotations
import os, io, zipfile, hmac
from datetime import date
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from core.schema import TABLES,validate,excel_template
from core.generator import generate
from core.repository import get_repository
from core.appearance import PALETTES, resolve_theme, stylesheet
from core.real_data import clean_uci_online_retail, summarize_uci_online_retail, SOURCE_URL
from core.analytics import (order_scope,sales_lines,sales_kpis,rfm_segments,cohort_retention,
marketing_performance,channel_performance,quality_snapshot,recommendations)

load_dotenv()
st.set_page_config(page_title="FD Intelligence | Commerce Analytics",page_icon="◈",layout="wide",initial_sidebar_state="expanded")
# Session-based appearance controls. System follows the browser-resolved Streamlit theme.
if "fd_color_mode" not in st.session_state:
    st.session_state.fd_color_mode = "System"
try:
    client_theme = st.context.theme.type
except (AttributeError, RuntimeError):
    client_theme = None
active_mode = resolve_theme(st.session_state.fd_color_mode, client_theme)
PALETTE = PALETTES[active_mode]
st.markdown(stylesheet(active_mode), unsafe_allow_html=True)

COLORS=["#D8AC69","#72C4B6","#819DF3","#E18D84","#BBA0D9","#A2BD77","#5AA5CC"]
def fmt_inr(x,dec=0): return f"₹{x:,.{dec}f}"
def fmt_inr_short(value):
    value = float(value)
    if abs(value)>=10_000_000: return f"₹{value/10_000_000:.2f} Cr"
    if abs(value)>=100_000: return f"₹{value/100_000:.2f} L"
    return fmt_inr(value)
def chart(fig,height=350):
    fig.update_layout(template=PALETTE["plotly"],height=height,margin=dict(l=25,r=18,t=52,b=28),
        paper_bgcolor=PALETTE["chart"],plot_bgcolor=PALETTE["chart"],
        font=dict(color=PALETTE["chart_text"],family="DM Sans"),
        colorway=COLORS,legend_title_text="")
    st.plotly_chart(fig,width="stretch",config={"displaylogo":False})
def empty_state(message="There are no records for these filters."): st.info(message)
def excel_bytes(dframes):
    b=io.BytesIO()
    with pd.ExcelWriter(b,engine="xlsxwriter") as writer:
        for name,df in dframes.items():df.to_excel(writer,sheet_name=name[:31],index=False)
    return b.getvalue()
def csv_download(label, df, filename):
    st.download_button(label,df.to_csv(index=False).encode("utf-8-sig"),file_name=filename,mime="text/csv")
def backup_bytes(ds,meta):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for name,df in ds.items():z.writestr(name+".csv",df.to_csv(index=False))
        z.writestr("DATA_PROVENANCE.txt", "FD E-Commerce Analytics Dataset Backup\n"+str(meta)+"\nVerify source documentation before claiming this is real-world FD store data.\n")
    return out.getvalue()

try:
    repo=get_repository()
    if not repo.has_data():
        st.error("This database is empty. Run `python seed.py` in the project folder, then refresh.")
        st.code("python seed.py\npython -m streamlit run app.py",language="powershell")
        st.stop()
    data=repo.load()
    metadata=repo.metadata()
except Exception as exc:
    st.error("Database connection or dataset loading failed. Review `.env` / MongoDB availability.")
    st.code(str(exc))
    st.stop()

min_dt=pd.to_datetime(data["orders"].order_date).min().date()
max_dt=pd.to_datetime(data["orders"].order_date).max().date()
regions=["All"]+sorted(data["customers"].region.unique().tolist())
categories=["All"]+sorted(data["products"].category.unique().tolist())
source=metadata.get("source","unknown/unverified")
admin_configured=bool(os.getenv("ADMIN_PASSWORD"))
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in=False
if not admin_configured:
    st.session_state.admin_logged_in = False

with st.sidebar:
    st.markdown("### ◈ FD / INTELLIGENCE")
    st.caption("Commerce performance command center")
    with st.expander("Appearance · Light / Dark / System", expanded=False):
        st.segmented_control("Color mode", options=["System", "Light", "Dark"],
                             selection_mode="single", key="fd_color_mode", label_visibility="collapsed")
        st.caption("System follows the Streamlit browser theme; session preference resets in a new browser session.")
    st.divider()
    page=st.radio("WORKSPACE",["Executive Overview","Sales Intelligence","Customer Intelligence","Campaign & ROI","Product Performance","Data Studio","Decision Lab","Real Data Explorer","Faculty Guide"],
        label_visibility="visible")
    st.divider()
    st.markdown("**GLOBAL SALES FILTERS**")
    dates=st.date_input("Sales date range",(min_dt,max_dt),min_value=min_dt,max_value=max_dt,help="Applied to sales and dashboard KPIs. Marketing spend uses selected dates nationally.")
    if not isinstance(dates,(tuple,list)) or len(dates)!=2:
        start,end=min_dt,max_dt
    else:
        start,end=dates
    region=st.selectbox("Customer region",regions)
    category=st.selectbox("Product category",categories)
    st.divider()
    st.caption("DATA ENGINE")
    st.write(f"**{repo.mode}**")
    st.caption(f"Source: {source}")
    st.caption(f"Last dataset import: {metadata.get('loaded_at_utc', 'unknown')}")
    if "synthetic" in source.lower():
        st.warning("SIMULATED DATA · NOT REAL STORE TRANSACTIONS")
    else:
        st.info("Imported dataset · provenance not independently verified")
    if st.button("Refresh current database snapshot", help="Re-read records already in MongoDB; does not fetch live sales from a store"):
        st.rerun()
    # Never render an administration entry point for a read-only cloud deployment.
    if admin_configured:
        with st.expander("Administrator workspace"):
            if st.session_state.admin_logged_in:
                st.success("Administrator unlocked")
                if st.button("Sign out",key="logout"):
                    st.session_state.admin_logged_in=False
                    st.rerun()
            else:
                pw=st.text_input("Admin password",type="password",key="admin_pw")
                if st.button("Unlock",key="unlock"):
                    if hmac.compare_digest(pw,os.getenv("ADMIN_PASSWORD","")):
                        st.session_state.admin_logged_in=True
                        st.rerun()
                    else:st.error("Incorrect password")
    st.caption("PCTE · Interdisciplinary Minor Project")

lines=sales_lines(data,start,end,region,category)
kpis=sales_kpis(lines)
all_region_lines=sales_lines(data,start,end,region,"All")
marketing=marketing_performance(data,start,end)  # National scope by design.
channels=channel_performance(marketing)
segments=rfm_segments(data,as_of=end,region=region)

st.markdown(f'''<div class="hero"><div class="eyebrow">FD / E-COMMERCE PERFORMANCE SYSTEM</div>
<h1>{page}</h1><p>Sales · Customer behavior · Campaign attribution · Business decisions</p>
<span class="tag">{repo.mode}</span><span class="tag" style="margin-left:8px">{start} → {end}</span></div>''',unsafe_allow_html=True)

if page=="Executive Overview":
    st.caption("Revenue = delivered order-line sales. Category filters apply to order lines; region filters apply to customers.")
    k1,k2,k3=st.columns(3)
    k1.metric("Delivered revenue",fmt_inr_short(kpis["revenue"]),help=f'Exact: {fmt_inr(kpis["revenue"])}')
    k2.metric("Selected orders",f'{kpis["orders"]:,}',help="Orders with at least one selected delivered item")
    k3.metric("Sales per selected order",fmt_inr_short(kpis["aov"]),help=f'Exact: {fmt_inr(kpis["aov"])}')
    k4,k5=st.columns(2)
    k4.metric("Unique buyers",f'{kpis["customers"]:,}')
    k5.metric("Units sold",f'{kpis["units"]:,}')
    if not lines.empty:
        left,right=st.columns([1.7,1])
        with left:
            mon=lines.assign(month=lines.order_date.dt.to_period("M").astype(str)).groupby("month",as_index=False).revenue.sum()
            fig=px.area(mon,x="month",y="revenue",title="Monthly realized revenue",markers=True,
                labels={"month":"Month","revenue":"Revenue (₹)"})
            fig.update_traces(line_color=COLORS[0],fillcolor="rgba(216,172,105,.2)")
            chart(fig,390)
        with right:
            cat=lines.groupby("category",as_index=False).revenue.sum()
            chart(px.pie(cat,names="category",values="revenue",hole=.65,title="Revenue composition",color_discrete_sequence=COLORS),390)
        a,b=st.columns(2)
        with a:
            region_df=lines.groupby("customer_id",as_index=False).revenue.sum().merge(data["customers"][["customer_id","region"]],on="customer_id")
            rg=region_df.groupby("region",as_index=False).revenue.sum().sort_values("revenue",ascending=False).head(8)
            chart(px.bar(rg,x="revenue",y="region",orientation="h",title="Top markets by realized sales",color="revenue",color_continuous_scale="Teal"),340)
        with b:
            top=lines.groupby("name",as_index=False).revenue.sum().nlargest(8,"revenue").sort_values("revenue")
            chart(px.bar(top,x="revenue",y="name",orientation="h",title="Top-performing products",color="revenue",color_continuous_scale="YlOrBr"),340)
    else:empty_state()
    st.subheader("Executive actions")
    for title,description in recommendations(data,lines,marketing,segments):
        st.markdown(f"**{title}** — {description}")

elif page=="Sales Intelligence":
    st.caption("Realized sales exclude shipped, cancelled and returned orders. Shipping and taxes are not modeled.")
    status=data["orders"][(data["orders"].order_date>=str(start))&(data["orders"].order_date<=str(end))].status.value_counts()
    a,b,c,d=st.columns(4)
    for col,stat in zip([a,b,c,d],["Delivered","Shipped","Cancelled","Returned"]):
        col.metric(stat+" orders",f"{int(status.get(stat,0)):,}")
    if not lines.empty:
        mon=lines.assign(month=lines.order_date.dt.to_period("M").astype(str)).groupby("month",as_index=False).agg(revenue=("revenue","sum"),units=("quantity","sum"),orders=("order_id","nunique"))
        chart(px.bar(mon,x="month",y="revenue",title="Realized monthly sales (₹)",color="revenue",color_continuous_scale="YlOrBr"),380)
        a,b=st.columns(2)
        with a:
            week=lines.assign(weekday=lines.order_date.dt.day_name()).groupby("weekday",as_index=False).revenue.sum()
            week["weekday"]=pd.Categorical(week.weekday,categories=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],ordered=True)
            week=week.sort_values("weekday")
            chart(px.bar(week,x="weekday",y="revenue",title="Weekday purchase pattern",color_discrete_sequence=[COLORS[1]]))
        with b:
            pay=lines.drop_duplicates("order_id").groupby("payment_method",as_index=False).order_id.count()
            chart(px.pie(pay,names="payment_method",values="order_id",title="Payment mix · selected delivered orders",hole=.4))
        st.subheader("Sales transactions")
        trans=lines.groupby(["order_id","order_date","customer_id"],as_index=False).agg(revenue=("revenue","sum"),units=("quantity","sum"))
        if st.session_state.admin_logged_in:
            st.dataframe(trans.sort_values("order_date",ascending=False),width="stretch",hide_index=True)
            csv_download("Export filtered sales lines · CSV (admin)",lines,"fd_sales_lines.csv")
            workbook={"Transactions":trans,"Monthly":mon}
        else:
            st.caption("Detailed order and customer identifiers are available only in a trusted administrator session.")
            st.dataframe(mon,width="stretch",hide_index=True)
            workbook={"Monthly":mon}
        st.download_button("Export sales analysis · Excel",excel_bytes(workbook),"fd_sales_analysis.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:empty_state()

elif page=="Customer Intelligence":
    st.caption("RFM uses each customer's entire delivered-order history up to the selected end date; the start-date and category filters do not alter that history.")
    a,b,c,d=st.columns(4)
    a.metric("Customers with delivered orders",f"{len(segments):,}")
    b.metric("Repeat buyers",f"{int((segments.frequency>=2).sum()):,}" if len(segments) else "0")
    c.metric("Repeat-buyer share",f"{100*(segments.frequency>=2).mean():.1f}%" if len(segments) else "0%")
    d.metric("At-risk + dormant",f"{int(segments.segment.isin(['At risk','Dormant']).sum()):,}")
    if len(segments):
        a,b=st.columns(2)
        with a:
            sg=segments.segment.value_counts().rename_axis("segment").reset_index(name="customers")
            chart(px.bar(sg,x="segment",y="customers",title="RFM behavioral segments",color="segment",color_discrete_sequence=COLORS),390)
        with b:
            chart(px.scatter(segments,x="recency",y="monetary",size="frequency",color="segment",opacity=.72,
                title="Recency vs customer lifetime spend",labels={"recency":"Days since latest order","monetary":"Delivered spend (₹)"},color_discrete_sequence=COLORS),390)
        st.subheader("Monthly customer cohort retention")
        st.caption("Percentage of each first-purchase cohort that purchases again in month 1, 2, etc. Later cohorts have fewer observable months.")
        cohorts=cohort_retention(data)
        if not cohorts.empty:
            cohorts=cohorts.iloc[-12:,:7]
            fig=px.imshow(cohorts,labels={"x":"Months after first order","y":"Acquisition cohort","color":"Retention %"},
                title="Delivered-order cohort retention (%)",text_auto=".0f",aspect="auto",color_continuous_scale="Teal")
            chart(fig,420)
        with st.expander("Optional unsupervised ML segmentation · K-Means"):
            st.caption("An exploratory clustering technique, not a proof of which segments are commercially optimal.")
            if len(segments)>=8:
                from sklearn.preprocessing import StandardScaler
                from sklearn.cluster import KMeans
                sample=segments[["recency","frequency","monetary"]]
                k=min(4,len(sample.drop_duplicates()))
                if k>=2:
                    labels=KMeans(n_clusters=k,n_init=10,random_state=42).fit_predict(StandardScaler().fit_transform(sample))
                    pts=segments.assign(cluster=labels.astype(str))
                    chart(px.scatter(pts,x="recency",y="monetary",size="frequency",color="cluster",title="ML clusters (numeric IDs only)"))
                else:empty_state("Not enough distinct behavior patterns to cluster.")
            else:empty_state("At least eight purchasing customers are needed for ML clusters.")
        if st.session_state.admin_logged_in:
            csv_download("Export RFM segments · CSV (admin)",segments,"fd_customer_rfm.csv")
            st.dataframe(segments.sort_values("monetary",ascending=False).head(100),hide_index=True,width="stretch")
        else:
            st.caption("Individual customer RFM records are restricted. Aggregated segments are available above.")
    else:empty_state("No delivered customer history before the selected end date.")

elif page=="Campaign & ROI":
    st.info("Marketing comparisons are national. **Region and category filters do not apply** to campaign spend or attribution, preventing incorrect regional ROI figures. Date-range spend is prorated by campaign days; impressions and clicks for partial windows are estimates.")
    active=marketing[marketing.allocated_spend>0]
    total_spend=float(active.allocated_spend.sum())
    total_rev=float(marketing.attributed_revenue.sum())
    total_margin=float(marketing.attributed_contribution.sum())
    total_conv=int(marketing.conversions.sum())
    a,b,c=st.columns(3)
    a.metric("Allocated ad spend",fmt_inr_short(total_spend),help=fmt_inr(total_spend))
    b.metric("Attributed revenue",fmt_inr_short(total_rev),help=fmt_inr(total_rev))
    c.metric("ROAS",f"{total_rev/total_spend:.2f}×" if total_spend else "—")
    d,e=st.columns(2)
    d.metric("Contribution ROI proxy",f"{(total_margin-total_spend)/total_spend*100:.1f}%" if total_spend else "—")
    e.metric("Attributed conversions",f"{total_conv:,}")
    if not channels.empty:
        a,b=st.columns([1.3,1])
        with a:
            long=channels.melt(id_vars="channel",value_vars=["spend","revenue"],var_name="series",value_name="amount")
            chart(px.bar(long,x="channel",y="amount",color="series",barmode="group",title="Channel spend vs attributed revenue",color_discrete_sequence=["#7B91B1",COLORS[0]]),390)
        with b:
            chart(px.bar(channels.sort_values("roas"),x="roas",y="channel",orientation="h",title="Revenue ROAS by channel",color="roas",color_continuous_scale="Teal"),390)
        st.subheader("Campaign-level performance")
        view=marketing[["name","channel","allocated_spend","attributed_revenue","attributed_contribution","conversions","cpa","roas","roi_proxy_pct","ctr_pct","cvr_pct"]].copy()
        st.dataframe(view,hide_index=True,width="stretch",column_config={
            "allocated_spend":st.column_config.NumberColumn("Allocated spend ₹",format="%.2f"),
            "attributed_revenue":st.column_config.NumberColumn("Attributed revenue ₹",format="%.2f"),
            "attributed_contribution":st.column_config.NumberColumn("Attributed contribution ₹",format="%.2f"),
            "roas":st.column_config.NumberColumn("ROAS ×",format="%.2f"),
            "roi_proxy_pct":st.column_config.NumberColumn("Contribution ROI %",format="%.1f"),
            "cpa":st.column_config.NumberColumn("CPA ₹",format="%.2f")})
        csv_download("Export campaign KPIs · CSV",view,"fd_campaign_performance.csv")
        st.download_button("Export campaign report · Excel",excel_bytes({"Campaigns":view,"Channels":channels}),"fd_marketing_roi.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with st.expander("Metric definitions: what can be claimed?"):
        st.markdown("""- **ROAS** = single-touch attributed delivered-order revenue / prorated campaign spend.
- **CPA** = allocated spend / attributed delivered-order count; not cost per newly acquired customer.
- **Contribution ROI proxy** = (attributed revenue - estimated product cost - allocated ad spend) / allocated ad spend × 100.
- **CTR** = estimated clicks / estimated impressions × 100; **CVR** = attributed conversions / estimated clicks × 100.
- Product costs are snapshots; payment fees, salaries, logistics, taxes, returns handling and multi-touch paths are **not modeled**. Do not claim this as audited net profit or causal ROI.
- **Attribution model:** one campaign maximum per delivered order. Organic/unattributed purchases are excluded from campaign-revenue totals.""")

elif page=="Product Performance":
    if not lines.empty:
        prod=lines.groupby(["product_id","name","category"],as_index=False).agg(units=("quantity","sum"),revenue=("revenue","sum"),product_cost=("cogs","sum"),contribution=("contribution","sum"))
        prod["margin_pct"]=np.where(prod.revenue>0,prod.contribution/prod.revenue*100,0)
        prod=prod.merge(data["products"][["product_id","stock"]],on="product_id",how="left")
        prod=prod.sort_values("revenue",ascending=False)
        prod["cumulative_pct"]=prod.revenue.cumsum()/prod.revenue.sum()*100
        prod["abc_class"]=np.select([prod.cumulative_pct<=80,prod.cumulative_pct<=95],["A","B"],default="C")
        a,b,c=st.columns(3)
        a.metric("Gross product contribution",fmt_inr(prod.contribution.sum()))
        b.metric("Product margin proxy",f"{100*prod.contribution.sum()/prod.revenue.sum():.1f}%")
        c.metric("Tracked SKUs in selection",len(prod))
        a,b=st.columns(2)
        with a:chart(px.bar(prod.head(12).sort_values("revenue"),x="revenue",y="name",orientation="h",title="Top products by realized revenue",color="category"))
        with b:chart(px.scatter(prod,x="revenue",y="margin_pct",size="units",hover_name="name",color="category",title="Product volume vs margin proxy"))
        st.caption("ABC classification is based on cumulative realized revenue for the selected scope. Stock levels are static demonstration snapshots, not live inventory ledger balances.")
        st.dataframe(prod,hide_index=True,width="stretch")
        csv_download("Export product insights · CSV",prod,"fd_product_performance.csv")
    else:empty_state()

elif page=="Data Studio":
    st.subheader("Operational health & lineage")
    q=quality_snapshot(data)
    a,b,c,d=st.columns(4)
    a.metric("Orders in database",f'{q["orders"]:,}')
    b.metric("Customers",f'{q["customers"]:,}')
    c.metric("Product SKUs",q["products"])
    d.metric("Campaign attributions",f'{q["attributed_orders"]:,}')
    st.info(f"Current source: **{source}** | Loaded UTC: **{metadata.get('loaded_at_utc','unknown')}** | Engine: **{repo.mode}**")
    with st.expander("Data dictionary and collection sizes",expanded=False):
        st.dataframe(pd.DataFrame([{"Collection":t,"Records":len(data[t]),
                    "Required fields":", ".join(TABLES[t])} for t in TABLES]),hide_index=True,width="stretch")
        if st.session_state.admin_logged_in:
            table=st.selectbox("Collection preview (admin)",list(TABLES))
            st.dataframe(data[table].head(50),width="stretch",hide_index=True)
    if st.session_state.admin_logged_in:
        with st.expander("Data audit trail (admin)"):
            st.dataframe(repo.audits(),width="stretch",hide_index=True)
    st.subheader("Import · export · database management")
    if not st.session_state.admin_logged_in:
        st.info("Database edits and sensitive exports are available only in a trusted local administrator session. The online dashboard stays read-only.")
    else:
        st.download_button("Backup complete database · 6 CSV tables + provenance",backup_bytes(data,metadata),
                           file_name="fd_full_database_backup.zip",mime="application/zip")
        st.download_button("Download blank Excel import template",excel_template(),file_name="fd_import_template.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with st.expander("A. Import all six tables (Excel workbook or six CSV files)",expanded=True):
            st.caption("All-or-nothing replacement: six tables required, referential integrity and order totals validated. Make a backup first. Imported source claims are self-reported, not independently verified.")
            mode=st.radio("Input type",["One Excel workbook (six sheets)","Six CSV files"],horizontal=True)
            uploads={}
            if mode.startswith("One"):
                f=st.file_uploader("Excel workbook with six named sheets",type=["xlsx"],key="data_xlsx")
                if f is not None:
                    try:
                        book=pd.read_excel(f,sheet_name=None,dtype={"order_id":str,"customer_id":str,"product_id":str,"campaign_id":str,"item_id":str,"attribution_id":str})
                        uploads={t:book[t] for t in TABLES}
                    except Exception as exc: st.error(f"Excel preparation failed: {exc}")
            else:
                for t in TABLES:
                    f=st.file_uploader(t+".csv",type=["csv"],key="csv_"+t)
                    if f is not None:
                        try:uploads[t]=pd.read_csv(f,dtype={k:str for k in ["order_id","customer_id","product_id","campaign_id","item_id","attribution_id"]})
                        except Exception as exc:st.error(f"{t} parsing failed: {exc}")
            source_note=st.text_input("Source and collection method",placeholder="Example: POS export supplied by store manager, 2026-09-30")
            confirm=st.checkbox("I made a backup and understand the existing dataset will be replaced")
            if uploads and len(uploads)==len(TABLES):
                try:
                    clean=validate(uploads)
                    st.success("All six tables passed validation: " + ", ".join(f"{k}: {len(v):,}" for k,v in clean.items()))
                    if st.button("Replace active dataset",type="primary",disabled=not (confirm and source_note.strip())):
                        repo.save(clean,source="user_import_unverified: "+source_note.strip()[:120],actor="dashboard_admin")
                        st.cache_data.clear()
                        st.success("New active dataset committed. Reloading...")
                        st.rerun()
                except Exception as exc:st.error(f"Dataset rejected: {exc}")
            elif uploads:
                st.info(f"Provided {len(uploads)} of {len(TABLES)} tables. Upload all six.")
        with st.expander("B. Generate a new realistic synthetic demonstration dataset"):
            st.warning("Generated names, orders, seasons and marketing events are SIMULATED, not independently obtained real-world transactions.")
            demo_seed=st.number_input("Repeatable random seed",min_value=0,max_value=2_000_000,value=42,step=1)
            nc=st.slider("Synthetic customers",100,3000,1250,50)
            no=st.slider("Synthetic orders",200,12000,5200,200)
            confirm_demo=st.checkbox("Replace the current dataset with a NEW simulated demonstration")
            if st.button("Generate and save dataset",disabled=not confirm_demo):
                with st.spinner("Generating and validating coherent transactions..."):
                    synth=generate(seed=int(demo_seed),n_customers=nc,n_orders=no)
                    repo.save(synth,source=f"synthetic_demo(seed={int(demo_seed)})",actor="dashboard_admin")
                st.success("Simulated data saved.")
                st.rerun()
    st.subheader("Data-quality rules")
    st.markdown("Unique record IDs; valid foreign keys; no negative prices or spends; clicks ≤ impressions; order totals reconciled with line items; valid campaign date windows; one campaign per delivered order; customer signup not after order; rejected imports leave the active dataset unchanged.")

elif page=="Decision Lab":
    st.subheader("Interpretable business recommendations")
    st.caption("Rule-based suggestions generated from actual active-dataset computations, not an AI model inventing conclusions.")
    for i,(title,description) in enumerate(recommendations(data,lines,marketing,segments),1):
        with st.container(border=True):st.markdown(f"**0{i} · {title}**");st.write(description)
    st.subheader("Marketing budget scenario (illustrative, not a revenue forecast)")
    if not channels.empty:
        choice=st.selectbox("Choose a marketing channel",channels.channel.tolist())
        proposed=st.slider("Hypothetical next-campaign budget (₹)",5000,200000,40000,5000)
        selected=channels[channels.channel.eq(choice)].iloc[0]
        st.metric("Historical attributed ROAS",f"{selected.roas:.2f}×" if pd.notna(selected.roas) else "N/A")
        potential=proposed*float(selected.roas) if pd.notna(selected.roas) else 0
        st.metric("Arithmetic scenario revenue · not a prediction",fmt_inr(potential))
        st.caption("Assumes identical historical ROAS despite different budget and seasonality. This is a what-if multiplication, not a causal forecast or promised result.")
    st.subheader("Definitions")
    st.markdown("**Data integration:** validated joins linking customers → orders → order items → products and campaigns → conversions → delivered orders.\n\n**Business intelligence:** turning these records into KPIs, customer cohorts, segments and comparable campaign metrics.\n\n**Actionability:** translating computed trends into testable strategic recommendations with stated assumptions.")

elif page=="Real Data Explorer":
    st.subheader("Authentic historical retail transactions")
    st.info("**REAL HISTORICAL DATA, NOT LIVE FD STORE DATA.** This explorer accepts the UCI Online Retail dataset (2010–2011, UK gift retailer). Original sales are in **GBP (£)**. Marketing spend, attribution and product costs are not available from this dataset.")
    st.markdown(f"[Get the publicly documented UCI Online Retail dataset]({SOURCE_URL}) · Source: Chen, D. (2015), UCI Online Retail, CC BY 4.0. Download **Online Retail.xlsx** from the source, then upload it here.")
    upload=st.file_uploader("Upload UCI Online Retail .xlsx or .csv (session-only; never written to MongoDB)",type=["xlsx","csv"],key="uci_file")
    if upload is not None:
        try:
            with st.spinner("Reading and checking authentic transaction records..."):
                raw=pd.read_excel(upload,dtype={"InvoiceNo":"string","StockCode":"string","CustomerID":"string"}) if upload.name.lower().endswith(".xlsx") else pd.read_csv(upload,dtype={"InvoiceNo":"string","StockCode":"string","CustomerID":"string"})
                real=clean_uci_online_retail(raw)
                summary=summarize_uci_online_retail(real)
            st.success(f"Analyzed {len(real):,} historical invoice lines from the uploaded file. No MongoDB data were replaced.")
            a,b,c=st.columns(3)
            a.metric("Gross realized sales (GBP)",f"£{summary['revenue']:,.0f}")
            b.metric("Sales invoices",f"{summary['invoices']:,}")
            c.metric("Cancellation / negative-quantity lines",f"{summary['cancelled_lines']:,}")
            a,b=st.columns([1.25,1])
            with a:chart(px.line(summary["monthly"],x="month",y="revenue_gbp",title="Monthly recorded sales (£)",markers=True),370)
            with b:chart(px.bar(summary["countries"].sort_values("revenue_gbp"),x="revenue_gbp",y="Country",orientation="h",title="Top customer countries (£)"),370)
            chart(px.bar(summary["products"].sort_values("revenue_gbp"),x="revenue_gbp",y="Description",orientation="h",title="Top products by value (£)"),400)
            st.download_button("Export aggregated monthly sales · CSV",summary["monthly"].to_csv(index=False).encode("utf-8"),file_name="uci_historical_monthly_gbp.csv",mime="text/csv")
            st.caption("Historical research data, not this fictional FD brand, not INR, and not live Shopify/marketplace orders. Blank customer identifiers remain missing; no customer names, ad spend, stock, acquisition dates, cost or attribution were invented.")
        except Exception as exc:
            st.error(f"Could not analyze the UCI file: {type(exc).__name__}: {exc}")
    st.divider()
    st.subheader("What is required for genuinely live FD sales?")
    st.markdown("Connect an **authorized real store** (for example Shopify GraphQL Admin API, WooCommerce REST API, or periodic POS exports) and separately integrate actual campaign spend/conversion records. Then validate them against the FD schema, keep a source audit trail and apply scheduled refreshes. A refresh button only reloads current MongoDB records; it does not create real transactions.")

elif page=="Faculty Guide":
    st.subheader("Live evaluation: 7-minute walkthrough")
    steps=[
        ("00:00 · Define the problem","Small sellers often have fragmented sales, customer and campaign files. This system validates and unifies six related datasets."),
        ("00:45 · Prove database integration","Open Data Studio. Show record counts, source and latest load. If MongoDB is enabled, identify that mode; otherwise correctly call this SQLite demo mode."),
        ("01:30 · Show dynamic filters","Change the date range, region and category. Point out which metrics change and why marketing remains national."),
        ("02:40 · Explain sales and buyers","Show time series, top products, delivered revenue, repeat-customer RFM, and cohort heatmap."),
        ("04:10 · Show marketing mathematics","Open Campaign & ROI. Explain ROAS, CPA, cost-based contribution ROI proxy, and single-touch attribution."),
        ("05:15 · Demonstrate data imports","Log in as admin, download template, show strict validations, show CSV/Excel exports and a full backup. Avoid replacing the live data unnecessarily."),
        ("06:30 · Discuss limits and future work","The FD database uses simulated data unless verified store exports are provided. Real Data Explorer can study genuine historical UK transactions separately, not live FD orders. There is no connected live commerce API or audited causal ROI.")]
    for title,body in steps:
        with st.expander(title,expanded=True):st.write(body)
    st.subheader("Project objective coverage")
    st.table(pd.DataFrame([
        ("Sales trends","Executive Overview + Sales Intelligence","Monthly, weekday, region and product charts"),
        ("Customer preferences","Customer Intelligence","RFM, cohorts, categories, payment types"),
        ("Marketing ROI","Campaign & ROI","ROAS, CPA, contribution ROI, date allocation"),
        ("Integrated data","Data Studio","Six linked tables; MongoDB option; strict imports"),
        ("Strategic decisions","Decision Lab","Rule-driven insights, scenario calculator"),
        ("Dynamic and exportable","Sidebar + Data Studio","Filtering, aggregate reports, admin-only raw exports and validated imports"),
        ("Authentic historical reference","Real Data Explorer","UCI Online Retail external file, GBP; explicitly not FD or live")],columns=["Faculty requirement","Where demonstrated","Evidence"]),hide_index=True)
    st.caption("Read docs/FACULTY_VIVA_GUIDE.md and docs/PROJECT_REPORT.md for methods, formulas, limitations, diagrams and questions.")

st.divider()
st.caption("FD Intelligence v2 · Academic analytics prototype · Source and last import shown in sidebar · FD demonstration currency: INR · Historical UCI reference currency: GBP")
