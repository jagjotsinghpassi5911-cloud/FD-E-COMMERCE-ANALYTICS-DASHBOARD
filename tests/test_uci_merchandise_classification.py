"""Regression checks for separate UCI product/service displays and unchanged totals."""
import pandas as pd
from core.real_data import clean_uci_online_retail, summarize_uci_online_retail, is_service_or_adjustment


def fixture_rows():
    return pd.DataFrame([
        {"InvoiceNo":"101","StockCode":"101A","Description":"CERAMIC JAR","Quantity":2,"InvoiceDate":"2011-01-02","UnitPrice":10,"Country":"UK"},
        {"InvoiceNo":"101","StockCode":"DOT","Description":"DOTCOM POSTAGE","Quantity":1,"InvoiceDate":"2011-01-02","UnitPrice":5,"Country":"UK"},
        {"InvoiceNo":"102","StockCode":"M","Description":"Manual","Quantity":1,"InvoiceDate":"2011-02-03","UnitPrice":3,"Country":"UK"},
        {"InvoiceNo":"C103","StockCode":"101A","Description":"CERAMIC JAR","Quantity":-1,"InvoiceDate":"2011-02-04","UnitPrice":10,"Country":"UK"},
    ])


def test_merchandise_only_rankings_do_not_lose_total_revenue():
    clean=clean_uci_online_retail(fixture_rows())
    summary=summarize_uci_online_retail(clean)
    assert summary['revenue']==28.0
    assert summary['service_revenue']==8.0
    assert summary['service_lines']==2
    assert summary['invoices']==2
    assert summary['cancelled_lines']==1
    assert summary['products']['Description'].tolist()==['CERAMIC JAR']
    assert summary['products']['revenue_gbp'].tolist()==[20.0]
    assert len(summary['monthly'])==2
    assert summary['period_start'].year==2011
    assert summary['period_end'].month==2


def test_classification_is_explicit_and_missing_descriptions_safe():
    table=pd.DataFrame({'StockCode':['POST','X3','M'],'Description':['Postage','GIFTS',pd.NA]})
    assert is_service_or_adjustment(table).tolist()==[True,False,True]
