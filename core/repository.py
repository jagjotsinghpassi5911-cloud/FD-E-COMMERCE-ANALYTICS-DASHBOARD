"""MongoDB primary production-style store; transactional SQLite local demo fallback."""
from __future__ import annotations
import os, json, uuid, sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from .schema import TABLES, validate

ROOT=Path(__file__).resolve().parents[1]

def utc_now(): return datetime.now(timezone.utc).isoformat()

class SQLiteRepository:
    mode="SQLite / offline demo"
    def __init__(self, path=None):
        self.path=Path(path or os.getenv("SQLITE_PATH",str(ROOT/"data"/"fd_demo.db")))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS fd_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS fd_audit (at_utc TEXT, action TEXT, actor TEXT, details TEXT)")
    def has_data(self):
        with sqlite3.connect(self.path) as conn:
            rows=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'").fetchall()
            return bool(rows)
    def load(self):
        if not self.has_data(): return None
        with sqlite3.connect(self.path) as conn:
            return {name:pd.read_sql_query(f'SELECT * FROM "{name}"',conn) for name in TABLES}
    def metadata(self):
        with sqlite3.connect(self.path) as conn:
            return dict(conn.execute("SELECT key,value FROM fd_metadata").fetchall())
    def save(self,raw,source="synthetic_demo",actor="seed_script"):
        data=validate(raw)
        with sqlite3.connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            for name, df in data.items():
                # pandas .to_sql with replace is not safely transactional; explicit DDL+INSERT is.
                conn.execute(f'DROP TABLE IF EXISTS "{name}"')
                columns=', '.join(f'"{c}" {"REAL" if pd.api.types.is_numeric_dtype(df[c]) else "TEXT"}' for c in df.columns)
                conn.execute(f'CREATE TABLE "{name}" ({columns})')
                placeholders=','.join(['?']*len(df.columns))
                conn.executemany(f'INSERT INTO "{name}" VALUES ({placeholders})', [tuple(x) for x in df.itertuples(index=False,name=None)])
            for key,value in {"source":source,"loaded_at_utc":utc_now(),"database":"sqlite","rows":json.dumps({t:len(d) for t,d in data.items()})}.items():
                conn.execute("INSERT OR REPLACE INTO fd_metadata VALUES (?,?)",(key,value))
            conn.execute("INSERT INTO fd_audit VALUES (?,?,?,?)",(utc_now(),"replace_dataset",actor,source))
        return self.metadata()
    def audits(self,limit=30):
        with sqlite3.connect(self.path) as conn:
            return pd.read_sql_query("SELECT * FROM fd_audit ORDER BY at_utc DESC LIMIT ?",conn,params=(limit,))

class MongoRepository:
    mode="MongoDB / persistent"
    def __init__(self,uri=None,db_name=None):
        from pymongo import MongoClient
        self.client=MongoClient(uri or os.environ.get("MONGODB_URI"),serverSelectionTimeoutMS=4000)
        self.client.admin.command("ping")
        self.db=self.client[db_name or os.getenv("MONGODB_DB","fd_ecommerce_analytics")]
    def metadata(self):
        doc=self.db.fd_metadata.find_one({"_id":"active"}) or {}
        return {k:v for k,v in doc.items() if k!="_id"}
    def has_data(self): return bool(self.metadata().get("batch_id"))
    def load(self):
        batch=self.metadata().get("batch_id")
        if not batch:return None
        data={}
        for table,cols in TABLES.items():
            records=list(self.db[table].find({"_fd_batch":batch},{"_id":0,"_fd_batch":0}))
            data[table]=pd.DataFrame.from_records(records,columns=cols)
        return data
    def save(self,raw,source="imported_real",actor="dashboard_admin"):
        data=validate(raw)
        batch=str(uuid.uuid4())
        written=[]
        try:
            for table, df in data.items():
                documents=[{**row,"_fd_batch":batch} for row in df.to_dict(orient="records")]
                if documents:self.db[table].insert_many(documents,ordered=True)
                written.append(table)
                self.db[table].create_index("_fd_batch")
            old=self.metadata().get("batch_id")
            meta={"batch_id":batch,"source":source,"loaded_at_utc":utc_now(),"database":"mongodb",
                  "rows":json.dumps({t:len(x) for t,x in data.items()})}
            # Last atomic step. Readers always see either old or new complete batch.
            self.db.fd_metadata.replace_one({"_id":"active"},{"_id":"active",**meta},upsert=True)
            self.db.fd_audit.insert_one({"at_utc":utc_now(),"action":"replace_dataset","actor":actor,"details":source,"batch_id":batch})
            if old:
                for table in TABLES:
                    self.db[table].delete_many({"_fd_batch":old})
            return self.metadata()
        except Exception:
            if self.metadata().get("batch_id")!=batch:
                for table in written:self.db[table].delete_many({"_fd_batch":batch})
            raise
    def audits(self,limit=30):
        records=list(self.db.fd_audit.find({}, {"_id":0}).sort("at_utc",-1).limit(limit))
        return pd.DataFrame.from_records(records,columns=["at_utc","action","actor","details","batch_id"])

def get_repository():
    backend=os.environ.get("DATA_BACKEND","sqlite").strip().lower()
    if backend=="sqlite": return SQLiteRepository()
    if backend=="mongodb":
        if not os.environ.get("MONGODB_URI"):
            raise RuntimeError("DATA_BACKEND=mongodb requires MONGODB_URI in .env")
        return MongoRepository()
    raise RuntimeError("DATA_BACKEND must be sqlite or mongodb")
