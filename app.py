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
from core.analytics import (order_scope,sales_lines,sales_kpis,rfm_segments,cohort_retention,
marketing_performance,channel_performance,quality_snapshot,recommendations)

load_dotenv()
st.set_page_config(page_title="FD E-Commerce Analytics Dashboard | Commerce Analytics",page_icon="◈",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif;}
h1,h2,h3 {font-family:'Manrope',sans-serif!important;letter-spacing:-.045em;}
.block-container{padding-top:1.5rem;padding-bottom:4rem;max-width:1700px;}
[data-testid="stMetric"]{background:linear-gradient(140deg,#1D2C42,#172236);border:1px solid #324056;padding:17px 20px;border-radius:16px;}
[data-testid="stMetricLabel"]{color:#A9BBD3}
[data-testid="stMetricValue"]{font-family:'Manrope';font-weight:800;font-size:1.75rem;}
[data-testid="stSidebar"]{background:#111B2D;border-right:1px solid #2B3950;}
[data-testid="stSidebar"] hr{border-color:#33435C}
[data-testid="stPlotlyChart"]{border:1px solid #2F4056;border-radius:15px;overflow:hidden;}
.stButton button[kind="primary"]{background:#D5A95F;color:#0E1726;font-weight:800;border:none;}
.hero{padding:25px 30px;border:1px solid #3C4A5D;background:linear-gradient(120deg,#233956 0%,#142237 70%,#122132 100%);border-radius:18px;margin-bottom:17px;}
.eyebrow{font-size:.76rem;font-weight:800;letter-spacing:.15em;color:#E3B869;text-transform:uppercase;}
.hero h1{font-weight:800;font-size:2.1rem;margin:.25rem 0;line-height:1.2;color:#F7FAFC}
.hero p{color:#B8C9DD;font-size:1rem;margin:.3rem 0 0}
.tag{display:inline-block;border:1px solid #9B7840;color:#F3C679;border-radius:7px;padding:4px 9px;font-size:.75rem;margin-top:13px}
[data-testid="stDataFrame"]{border:1px solid #2C3951;border-radius:10px;}
</style>""",unsafe_allow_html=True)

COLORS=["#D8AC69","#72C4B6","#819DF3","#E18D84","#BBA0D9","#A2BD77","#5AA5CC"]
def fmt_inr(x,dec=0): return f"₹{x:,.{dec}f}"
def chart(fig,height=350):
    fig.update_layout(template="plotly_dark",height=height,margin=dict(l=25,r=18,t=52,b=28),
        paper_bgcolor="#101827",plot_bgcolor="#101827",font=dict(color="#D5DEEB",family="DM Sans"),
        colorway=COLORS,legend_title_text="")
    st.plotly_chart(fig,use_container_width=True,config={"displaylogo":False})
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

with st.sidebar:
    st.markdown("### ◈ FD E-Commerce Analytics Dashboard")
    st.caption("Commerce performance command center")
    st.divider()
    page=st.radio("WORKSPACE",["Executive Overview","Sales Intelligence","Customer Intelligence","Campaign & ROI","Product Performance","Data Studio","Decision Lab","Faculty Guide"],
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
    if source.startswith("synthetic_demo"):
        st.warning("SIMULATED DATA · NOT REAL STORE TRANSACTIONS")
    else:
        st.info("Imported dataset · provenance not independently verified")
    with st.expander("Administrator access"):
        if st.session_state.admin_logged_in:
            st.success("Administrator unlocked")
            if st.button("Sign out",key="logout"):
                st.session_state.admin_logged_in=False
                st.rerun()
        elif not admin_configured:
            st.caption("Set ADMIN_PASSWORD in .env to enable editing and raw-data export.")
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

st.markdown(f'''<div class="hero"><div class="eyebrow">FD / E-COMMERCE ANALYTICS DASHBOARD</div>
<h1>{page}</h1><p>Sales · Customer behavior · Campaign attribution · Business decisions</p>
<span class="tag">{repo.mode}</span><span class="tag" style="margin-left:8px">{start} → {end}</span></div>''',unsafe_allow_html=True)

if page=="Executive Overview":
    st.caption("Revenue = delivered order-line sales. Category filters apply to order lines; region filters apply to customers.")
    k1,k2,k3,k4,k5=st.columns(5)
    k1.metric("Delivered revenue",fmt_inr(kpis["revenue"]))
    k2.metric("Orders containing selection",f'{kpis["orders"]:,}')
    k3.metric("Sales per selected order",fmt_inr(kpis["aov"]))
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
        st.dataframe(trans.sort_values("order_date",ascending=False),use_container_width=True,hide_index=True)
        csv_download("Export filtered sales lines · CSV",lines,"fd_sales_lines.csv")
        st.download_button("Export sales analysis · Excel",excel_bytes({"Transactions":trans,"Monthly":mon}),"fd_sales_analysis.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
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
                sample=segments[["recency","frequency", run"monetary"]]
                k=min(4,len(sample.drop_duplicates()))
                if k>=2:
                    labels=KMeans(n_clusters=k,n_init=10,random_state=42).fit_predict(StandardScaler().fit_transform(sample))
                    pts=segments.assign(cluster=labels.astype(str))
                    chart(px.scatter(pts,x="recency",y="monetary",size="frequency",color="cluster",title="ML clusters (numeric IDs only)"))
                else:empty_state("Not enough distinct behavior patterns to cluster.")
            else:empty_state("At least eight purchasing customers are needed for ML clusters.")
        csv_download("Export RFM segments · CSV",segments,"fd_customer_rfm.csv")
        st.dataframe(segments.sort_values("monetary",ascending=False).head(100),hide_index=True,use_container_width=True)
    else:empty_state("No delivered customer history before the selected end date.")

elif page=="Campaign & ROI":
    st.info("Marketing comparisons are national. **Region and category filters do not apply** to campaign spend or attribution, preventing incorrect regional ROI figures. Date-range spend is prorated by campaign days; impressions and clicks for partial windows are estimates.")
    active=marketing[marketing.allocated_spend>0]
    total_spend=float(active.allocated_spend.sum())
    total_rev=float(marketing.attributed_revenue.sum())
    total_margin=float(marketing.attributed_contribution.sum())
    total_conv=int(marketing.conversions.sum())
    a,b,c,d,e=st.columns(5)
    a.metric("Allocated ad spend",fmt_inr(total_spend))
    b.metric("Attributed revenue",fmt_inr(total_rev))
    c.metric("ROAS",f"{total_rev/total_spend:.2f}×" if total_spend else "—")
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
        st.dataframe(view,hide_index=True,use_container_width=True,column_config={
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
        st.dataframe(prod,hide_index=True,use_container_width=True)
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
    with st.expander("Data dictionary and table previews",expanded=False):
        table=st.selectbox("Collection / table",list(TABLES))
        st.write("Required fields:",", ".join(TABLES[table]))
        preview=data[table].head(50).copy()
        if table=="customers" and not st.session_state.admin_logged_in:
            preview["name"]="[masked — admin access required]"
        st.dataframe(preview,use_container_width=True,hide_index=True)
    with st.expander("Data audit trail"):
        st.dataframe(repo.audits(),use_container_width=True,hide_index=True)
    st.subheader("Import · export · database management")
    if not st.session_state.admin_logged_in:
        st.warning("Data modification and raw personal-data export require administrator access in the sidebar. Set ADMIN_PASSWORD in .env first.")
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

elif page=="Faculty Guide":
    st.subheader("Live evaluation: 7-minute walkthrough")
    steps=[
        ("00:00 · Define the problem","Small sellers often have fragmented sales, customer and campaign files. This system validates and unifies six related datasets."),
        ("00:45 · Prove database integration","Open Data Studio. Show record counts, source and latest load. If MongoDB is enabled, identify that mode; otherwise correctly call this SQLite demo mode."),
        ("01:30 · Show dynamic filters","Change the date range, region and category. Point out which metrics change and why marketing remains national."),
        ("02:40 · Explain sales and buyers","Show time series, top products, delivered revenue, repeat-customer RFM, and cohort heatmap."),
        ("04:10 · Show marketing mathematics","Open Campaign & ROI. Explain ROAS, CPA, cost-based contribution ROI proxy, and single-touch attribution."),
        ("05:15 · Demonstrate data imports","Log in as admin, download template, show strict validations, show CSV/Excel exports and a full backup. Avoid replacing the live data unnecessarily."),
        ("06:30 · Discuss limits and future work","This is a transparent proof-of-concept. Data are generated unless explicitly imported; no payment integration, live commerce API, verified causal marketing uplift, or audited profit accounting.")]
    for title,body in steps:
        with st.expander(title,expanded=True):st.write(body)
    st.subheader("Project objective coverage")
    st.table(pd.DataFrame([
        ("Sales trends","Executive Overview + Sales Intelligence","Monthly, weekday, region and product charts"),
        ("Customer preferences","Customer Intelligence","RFM, cohorts, categories, payment types"),
        ("Marketing ROI","Campaign & ROI","ROAS, CPA, contribution ROI, date allocation"),
        ("Integrated data","Data Studio","Six linked tables; MongoDB option; strict imports"),
        ("Strategic decisions","Decision Lab","Rule-driven insights, scenario calculator"),
        ("Dynamic and exportable","Sidebar + Data Studio","Filtering, Excel/CSV export, backup, validation")],columns=["Faculty requirement","Where demonstrated","Evidence"]),hide_index=True)
    st.caption("Read docs/FACULTY_VIVA_GUIDE.md and docs/PROJECT_REPORT.md for methods, formulas, limitations, diagrams and questions.")

st.divider()
st.caption("FD Intelligence · Academic analytics prototype · Transactional and attribution data provenance shown in sidebar · INR currency · Reporting date depends on imported dataset")
