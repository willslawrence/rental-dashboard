#!/usr/bin/env python3
"""
Generate data.json from CSV source files.
CSVs are the source of truth — never hand-edit data.json.
This script outputs RAW data only. All math (NOI, cash flow, ratios, ROI)
is computed by the browser in index.html.

Usage: python3 generate_dashboard.py
"""

import json, csv, os
from datetime import date

CSV_DIR = os.path.expanduser("~/.openclaw/workspace-renti/csvs")
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

PROPERTIES = {
    "talbot": {"name": "Talbot", "address": "2129 Talbot Street, Toledo, OH 43613", "status": "operating", "rent": 1450, "petFee": 0, "manager": "TPM Realty"},
    "bellevue": {"name": "Bellevue", "address": "3901 Bellevue Rd, Toledo, OH 43613", "status": "operating", "rent": 1595, "petFee": 20, "manager": "TPM Realty"},
    "boone": {"name": "Boone", "address": "1805 W Boone Ave, Spokane, WA 99201", "status": "operating", "rent": 1695, "petFee": 50, "manager": "Domaci"},
    "monroe": {"name": "Monroe", "address": "6810 N Monroe St, Spokane, WA 99208", "status": "operating", "rent": 2295, "petFee": 0, "manager": "Domaci"},
}

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def sort_month(month_str):
    parts = month_str.split()
    return (2000 + int(parts[1]), MONTH_NAMES.index(parts[0]))

def load_csv(prop_id):
    path = os.path.join(CSV_DIR, f"{prop_id}.csv")
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            occ = row.get("occupancy", "")
            if occ == "":
                occ = 1.0 if float(row["income"]) > 0 else 0.0
            else:
                occ = float(occ)
            rows.append({
                "month": row["month"],
                "income": float(row["income"]),
                "expenses": float(row["expenses"]),
                "mortgage": float(row["mortgage"]),
                "occupancy": occ,
                "notes": row.get("notes", ""),
            })
    rows.sort(key=lambda r: sort_month(r["month"]))
    return rows

def load_purchase_data():
    path = os.path.join(CSV_DIR, "purchase_data.json")
    with open(path) as f:
        return json.load(f)

def build_property(prop_id, config, monthly, purchase_info):
    pur = purchase_info.get("purchase", {})
    loan = purchase_info.get("loan", {})
    val = purchase_info.get("valuation", {})

    return {
        "id": prop_id,
        "name": config["name"],
        "address": config["address"],
        "status": config["status"],
        "purchase": pur,
        "loan": loan,
        "valuation": val,
        "operations": {
            "rent": config["rent"],
            "petFee": config["petFee"],
            "manager": config["manager"],
            "monthly": monthly,
        },
    }

def main():
    purchase_data = load_purchase_data()
    properties = []
    for prop_id, config in PROPERTIES.items():
        monthly = load_csv(prop_id)
        pinfo = purchase_data.get(prop_id, {})
        prop = build_property(prop_id, config, monthly, pinfo)
        properties.append(prop)

    total_value = sum(p["valuation"].get("currentValue", 0) or 0 for p in properties)
    total_equity = sum(p["valuation"].get("equity", 0) or 0 for p in properties)
    total_invested = sum(p["purchase"].get("totalInvested", 0) or 0 for p in properties)

    data = {
        "lastUpdated": date.today().isoformat(),
        "generatedFrom": "generate_dashboard.py from CSV source files",
        "portfolio": {
            "totalValue": total_value,
            "totalEquity": total_equity,
            "totalInvested": total_invested,
        },
        "properties": properties,
    }

    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Generated {OUTPUT}")
    for p in properties:
        n = len(p["operations"]["monthly"])
        print(f"  {p['name']}: {n} months of data")

if __name__ == "__main__":
    main()
