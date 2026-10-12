import math
import pytest
import pandas as pd
from core.generator import generate
from core.schema import validate
from core.analytics import order_scope,sales_lines,sales_kpis,marketing_performance,channel_performance,rfm_segments,cohort_retention
from core.repository import SQLiteRepository

@pytest.fixture(scope="module")
def ds():return generate(seed=15,n_customers=120,n_orders=350)

def test_generator_reproducible(ds):
    second=generate(seed=15,n_customers=120,n_orders=350)
    for key in ds:pd.testing.assert_frame_equal(ds[key],second[key])

def test_integrity_and_total(ds):
    validate(ds)
    delivery=ds['orders'].query('status == "Delivered"').total_amount.sum()
    assert math.isclose(sales_lines(ds).revenue.sum(),delivery,abs_tol=.01)
    assert math.isclose(sales_kpis(sales_lines(ds))['revenue'],delivery,abs_tol=.01)

def test_cancelled_and_returned_excluded(ds):
    delivered=set(order_scope(ds).order_id)
    assert set(sales_lines(ds).order_id).issubset(delivered)
    assert not (set(ds['orders'].query('status != "Delivered"').order_id) & delivered)

def test_filters_preserve_category_line_amount(ds):
    total=sales_kpis(sales_lines(ds))['revenue']
    parts=sum(sales_kpis(sales_lines(ds,category=c))['revenue'] for c in ds['products'].category.unique())
    assert math.isclose(total,parts,abs_tol=.01)

def test_marketing_single_touch_and_spend(ds):
    performance=marketing_performance(ds)
    assert int(performance.conversions.sum()) == len(ds['campaign_conversions'])
    assert math.isclose(float(performance.allocated_spend.sum()),float(ds['marketing_campaigns'].spend.sum()),abs_tol=.1)
    assert math.isclose(float(channel_performance(performance).revenue.sum()),float(performance.attributed_revenue.sum()),abs_tol=.01)

def test_marketing_partial_spend(ds):
    perf=marketing_performance(ds,'2025-05-02','2025-05-09')
    assert (perf.allocated_spend<=perf.spend).all()
    assert (perf.allocated_spend>=0).all()
    assert float(perf.allocated_spend.sum()) < float(ds['marketing_campaigns'].spend.sum())

def test_rfm_and_cohorts(ds):
    seg=rfm_segments(ds)
    assert set(seg.segment).issubset({'Champions','Loyal','At risk','Dormant','One-time','Growing'})
    assert (seg.frequency>=1).all()
    cohorts=cohort_retention(ds)
    assert not cohorts.empty
    assert (cohorts[0]==100).all()

def test_inconsistent_order_amount_rejected(ds):
    copy={k:v.copy() for k,v in ds.items()}
    copy['orders'].loc[0,'total_amount']+=1000
    with pytest.raises(ValueError,match='does not equal'):validate(copy)

def test_invalid_campaign_customer_rejected(ds):
    copy={k:v.copy() for k,v in ds.items()}
    copy['campaign_conversions'].loc[0,'customer_id']='not-customer'
    with pytest.raises(ValueError,match='does not match'):validate(copy)

def test_sqlite_roundtrip_and_atomic_invalid_rollback(ds,tmp_path):
    repo=SQLiteRepository(tmp_path/'store.db')
    repo.save(ds,source='synthetic_demo(TEST)',actor='test_suite')
    saved=repo.load()
    assert len(saved['orders'])==len(ds['orders'])
    assert repo.metadata()['source']=='synthetic_demo(TEST)'
    assert len(repo.audits())==1
    bad={k:v.copy() for k,v in ds.items()}
    bad['order_items'].loc[0,'order_id']='NOT_REAL'
    with pytest.raises(ValueError):repo.save(bad)
    assert len(repo.load()['orders'])==len(ds['orders'])
