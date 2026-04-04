#!/usr/bin/env python3
"""Update data.json with corrected/new March 2026 data from Appfolio PDFs."""
import json
from datetime import date

with open('/tmp/rental-dashboard/data.json') as f:
    data = json.load(f)

for p in data['properties']:
    pid = p['id']
    monthly = p['operations']['monthly']
    
    if pid == 'talbot':
        # Fix Mar 26 - was "clean month $145" but actually has $6,200 furnace replacement
        for m in monthly:
            if m['month'] == 'Mar 26':
                m['income'] = 1450.0
                m['expenses'] = 6890.65  # mgmt $145 + supplies $10.65 + thermocouple $225 + furnace $6200 + markup $310
                m['mortgage'] = 854.06
                m['occupancy'] = 1.0
                m['notes'] = "Water heater thermocouple $225 + supplies $10.65. FURNACE REPLACEMENT $6,200 + markup $310 (Thompson Plumbing). Owner disbursement $2,623.73"
                m['noi'] = m['income'] - m['expenses']
                m['cashFlow'] = m['noi'] - m['mortgage']
                print(f"  FIXED talbot Mar 26: expenses={m['expenses']}, NOI={m['noi']}, CF={m['cashFlow']}")
    
    elif pid == 'bellevue':
        # Fix Mar 26 - income was 1613, should be 1615; expenses were 159.50, should be 161.50
        for m in monthly:
            if m['month'] == 'Mar 26':
                m['income'] = 1615.0
                m['expenses'] = 161.5  # mgmt $159.50 + pet fee $2.00
                m['mortgage'] = 781.0
                m['occupancy'] = 1.0
                m['notes'] = "Rent $1,595 + pet $20. Clean month."
                m['noi'] = m['income'] - m['expenses']
                m['cashFlow'] = m['noi'] - m['mortgage']
                print(f"  FIXED bellevue Mar 26: income={m['income']}, expenses={m['expenses']}")
    
    elif pid == 'boone':
        # Add Mar 26
        mar = {
            "month": "Mar 26",
            "income": 1745.0,  # rent $1,685 + pet $50 + prepayment $10
            "expenses": 223.6,  # mgmt $1 + mgmt $173.50 + maintenance $49.10 (RMB Handyman)
            "mortgage": 1266.0,
            "occupancy": 1.0,
            "notes": "Rent $1,685 + pet $50 + prepayment $10. General maintenance $49.10 (RMB Handyman).",
        }
        mar['noi'] = mar['income'] - mar['expenses']
        mar['cashFlow'] = mar['noi'] - mar['mortgage']
        monthly.append(mar)
        print(f"  ADDED boone Mar 26: NOI={mar['noi']}, CF={mar['cashFlow']}")
    
    elif pid == 'monroe':
        # Add Mar 26
        mar = {
            "month": "Mar 26",
            "income": 2200.0,  # single payment $2,200
            "expenses": 220.0,  # mgmt $220
            "mortgage": 1608.0,
            "occupancy": 1.0,
            "notes": "Single rent payment $2,200. Mgmt $220.",
        }
        mar['noi'] = mar['income'] - mar['expenses']
        mar['cashFlow'] = mar['noi'] - mar['mortgage']
        monthly.append(mar)
        print(f"  ADDED monroe Mar 26: NOI={mar['noi']}, CF={mar['cashFlow']}")

    # Recalculate operations summary
    operating = [m for m in monthly if m['income'] > 0]
    n = len(operating)
    if n > 0:
        p['operations']['monthlyNOI'] = round(sum(m['noi'] for m in operating) / n, 2)
        p['operations']['monthlyCashFlow'] = round(sum(m['cashFlow'] for m in operating) / n, 2)
        p['operations']['annualNOI'] = round(p['operations']['monthlyNOI'] * 12, 2)
        avg_income = sum(m['income'] for m in operating) / n
        avg_expenses = sum(m['expenses'] for m in operating) / n
        p['operations']['expenseRatio'] = round(avg_expenses / avg_income * 100, 1) if avg_income > 0 else 0
        p['operations']['dataMonths'] = len(monthly)

# Recalculate portfolio totals
total_noi = sum(p['operations']['monthlyNOI'] for p in data['properties'])
total_mortgage = sum(p['operations'].get('monthly', [{}])[-1].get('mortgage', 0) for p in data['properties'])
data['portfolio']['totalMonthlyNOI'] = round(total_noi, 2)
data['portfolio']['totalMonthlyMortgage'] = round(total_mortgage, 2)
data['portfolio']['totalMonthlyCashFlow'] = round(total_noi - total_mortgage, 2)

data['lastUpdated'] = date.today().isoformat()

with open('/tmp/rental-dashboard/data.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"\nDone. Updated {data['lastUpdated']}")
print(f"Portfolio: NOI=${data['portfolio']['totalMonthlyNOI']}/mo, CF=${data['portfolio']['totalMonthlyCashFlow']}/mo")
