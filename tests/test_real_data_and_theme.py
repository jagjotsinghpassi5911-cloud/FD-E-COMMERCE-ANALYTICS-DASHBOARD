import pandas as pd
import pytest
from core.appearance import resolve_theme, stylesheet
from core.real_data import clean_uci_online_retail, summarize_uci_online_retail


def sample():
    return pd.DataFrame([
        {"InvoiceNo":"1001","StockCode":"S1","Description":"Tea cup","Quantity":2,"InvoiceDate":"2011-03-01 10:00","UnitPrice":5.0,"CustomerID":"1","Country":"United Kingdom"},
        {"InvoiceNo":"1001","StockCode":"S2","Description":"Dish","Quantity":1,"InvoiceDate":"2011-03-01 10:00","UnitPrice":12.0,"CustomerID":"1","Country":"United Kingdom"},
        {"InvoiceNo":"C1002","StockCode":"S1","Description":"Tea cup","Quantity":-1,"InvoiceDate":"2011-03-02 10:00","UnitPrice":5.0,"CustomerID":"1","Country":"United Kingdom"},
        {"InvoiceNo":"1003","StockCode":"S3","Description":"Gift","Quantity":1,"InvoiceDate":"2011-03-03 10:00","UnitPrice":0.0,"CustomerID":None,"Country":"France"},
    ])


def test_uci_realized_revenue_excludes_cancellations():
    d=clean_uci_online_retail(sample())
    out=summarize_uci_online_retail(d)
    assert out['revenue']==22.0
    assert out['invoices']==2
    assert out['cancelled_lines']==1
    assert out['customers']==1
    assert out['monthly'].iloc[0]['revenue_gbp']==22.0


def test_uci_missing_required_columns_rejected():
    with pytest.raises(ValueError,match='Missing'):
        clean_uci_online_retail(pd.DataFrame({'InvoiceNo':['1']}))


def test_appearance_modes():
    assert resolve_theme('System','light')=='Light'
    assert resolve_theme('System','dark')=='Dark'
    assert resolve_theme('Dark','light')=='Dark'
    assert resolve_theme('Light','dark')=='Light'
    assert 'background' in stylesheet('Light')
    assert 'background' in stylesheet('Dark')
