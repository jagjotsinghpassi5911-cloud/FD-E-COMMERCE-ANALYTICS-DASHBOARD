"""Seed the configured database with clearly labeled synthetic demonstration data."""
import argparse
from dotenv import load_dotenv
from core.generator import generate
from core.repository import get_repository
load_dotenv()

def main():
    p=argparse.ArgumentParser(description="Generate and load SYNTHETIC demonstration transactions")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--customers",type=int,default=1250)
    p.add_argument("--orders",type=int,default=5200)
    a=p.parse_args()
    ds=generate(seed=a.seed,n_customers=a.customers,n_orders=a.orders)
    repo=get_repository()
    print("Database:",repo.mode)
    print("Dataset provenance: SYNTHETIC DEMONSTRATION, NOT VERIFIED REAL STORE DATA")
    print("Rows:",{name:len(df) for name,df in ds.items()})
    repo.save(ds,source=f"synthetic_demo(seed={a.seed})",actor="seed_script")
    print("Seed completed successfully.")

if __name__=="__main__": main()
