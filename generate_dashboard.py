#!/usr/bin/env python3
"""
Generate data.json from CSV source files.
CSVs are the source of truth — never hand-edit data.json.

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
    n = len(monthly)
    total_income = sum(m["income"] for m in monthly)
    total_expenses = sum(m["expenses"] for m in monthly)
    avg_income = total_income / n if n > 0 else 0
    avg_expenses = total_expenses / n if n > 0 else 0
    avg_noi = avg_income - avg_expenses
    avg_mortgage = sum(m["mortgage"] for m in monthly) / n if n > 0 else 0
    avg_cf = avg_noi - avg_mortgage
    total_occupancy = sum(m["occupancy"] for m in monthly)
    occupancy = round((total_occupancy / n) * 100, 1) if n > 0 else 0

    for m in monthly:
        m["noi"] = round(m["income"] - m["expenses"], 2)
        m["cashFlow"] = round(m["income"] - m["expenses"] - m["mortgage"], 2)

    pur = purchase_info.get("purchase", {})
    loan = purchase_info.get("loan", {})
    val = purchase_info.get("valuation", {})

    # ROI calculations (cash flow + appreciation vs total invested)
    invested = pur.get("totalInvested", 0) or 0
    current_value = val.get("currentValue", 0) or 0
    total_cf = sum(m["cashFlow"] for m in monthly)
    appreciation = current_value - (pur.get("price", 0) or 0)
    total_return = total_cf + appreciation
    roi = round((total_return / invested) * 100, 1) if invested > 0 else 0
    annualized_roi = round((roi / n) * 12, 1) if n > 0 and invested > 0 else 0

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
            "monthlyNOI": round(avg_noi, 2),
            "monthlyCashFlow": round(avg_cf, 2),
            "annualNOI": round(avg_noi * 12, 2),
            "expenseRatio": round((avg_expenses / avg_income * 100), 1) if avg_income > 0 else 0,
            "occupancy": occupancy,
            "roi": roi,
            "annualizedRoi": annualized_roi,
            "manager": config["manager"],
            "dataMonths": n,
            "dataRange": "",
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

    total_noi = sum(p["operations"]["monthlyNOI"] for p in properties)
    total_mortgage = sum(p["loan"].get("totalPayment", 0) or p["loan"].get("payment", 0) or 0 for p in properties)
    total_cf = total_noi - total_mortgage
    total_value = sum(p["valuation"].get("currentValue", 0) or 0 for p in properties)
    total_equity = sum(p["valuation"].get("equity", 0) or 0 for p in properties)
    total_invested = sum(p["purchase"].get("totalInvested", 0) or 0 for p in properties)

    data = {
        "lastUpdated": date.today().isoformat(),
        "generatedFrom": "generate_dashboard.py from CSV source files",
        "portfolio": {
            "totalMonthlyNOI": round(total_noi, 2),
            "totalMonthlyMortgage": round(total_mortgage, 2),
            "totalMonthlyCashFlow": round(total_cf, 2),
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
        ops = p["operations"]
        print(f"  {p['name']}: {ops['dataMonths']}mo, NOI ${ops['monthlyNOI']:,.0f}/mo, CF ${ops['monthlyCashFlow']:,.0f}/mo, Occ {ops['occupancy']}%")
    print(f"  Portfolio: NOI ${total_noi:,.0f}, Mort ${total_mortgage:,.0f}, CF ${total_cf:,.0f}")

if __name__ == "__main__":
    main()
