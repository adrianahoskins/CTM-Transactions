"""Build GMA-only (Les Grands Moulins d'Abidjan) transaction dashboard."""
import json
from datetime import datetime
from collections import defaultdict

with open('ctm_data.json', 'r') as f:
    data = json.load(f)

rate = data['rate']
all_transfers = data.get('transfers', [])

# Filter transactions to GMA only
transactions = [t for t in data['transactions'] if 'GMA' in t['account'].upper()]
transactions.sort(key=lambda x: x['date'])

# Filter transfers to GMA only (both sides must involve GMA accounts)
transfers = [t for t in all_transfers
             if 'GMA' in t.get('source_account', '').upper() or 'GMA' in t.get('dest_account', '').upper()]

# Bank display name normalization
BANK_DISPLAY = {
    'AFG BK': 'AFG Bank (Africa Financial Group)',
    'BANQUE POPULAIRE': 'Banque Populaire CI',
    'Bank Atlantique IC': 'Banque Atlantique Ivory Coast',
    'BOA Ivory Coast': 'BOA Ivory Coast',
    'SOCGEN Ivory Coast': 'Societe Generale Ivory Coast',
    'SIB (IVORIAN BANK)': 'SIB (Societe Ivoirienne de Banque)',
    'MTN Mobile FS CI': 'MTN Mobile Money CI',
    'CITI IVORY COAST': 'Citibank Ivory Coast',
    'STANBIC IVORY COAST': 'Stanbic Bank Ivory Coast',
    'BICIS Senegal': 'BICIS Senegal',
    'Bank Atlantique SN': 'Banque Atlantique Senegal',
    'C.B.A.O. Senegal': 'CBAO Senegal',
    'Bank Africa Senegal': 'Bank of Africa Senegal',
    'SOCGEN SENEGAL BNK': 'Societe Generale Senegal',
    'Citi Senegal Bank': 'Citibank Senegal',
}

def bdn(name):
    return BANK_DISPLAY.get(name, name)

def fmt_net(val):
    if val >= 0:
        return f'+{val:,.0f}'
    else:
        return f'{val:,.0f}'

# Recompute all stats from filtered transactions
total_count = len(transactions)
cat_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
bank_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
month_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
flow_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
acct_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0, 'bank': ''})

for t in transactions:
    for stats, key in [(cat_stats, t['category']), (bank_stats, t['bank']),
                       (month_stats, t['month']), (flow_stats, t['flow_type'])]:
        stats[key]['count'] += 1
        if t['amount_xof'] < 0:
            stats[key]['debit_xof'] += t['amount_xof']
        else:
            stats[key]['credit_xof'] += t['amount_xof']
    acct_stats[t['account']]['count'] += 1
    acct_stats[t['account']]['bank'] = t['bank']
    if t['amount_xof'] < 0:
        acct_stats[t['account']]['debit_xof'] += t['amount_xof']
    else:
        acct_stats[t['account']]['credit_xof'] += t['amount_xof']

# Totals
total_debit_xof = sum(s['debit_xof'] for s in cat_stats.values())
total_credit_xof = sum(s['credit_xof'] for s in cat_stats.values())
total_debit_usd = total_debit_xof / rate
total_credit_usd = total_credit_xof / rate
net_xof = total_credit_xof + total_debit_xof
net_usd = net_xof / rate

# Category rows
cat_rows = ''
for cat, s in sorted(cat_stats.items(), key=lambda x: -x[1]['count']):
    d_usd = s['debit_xof'] / rate
    c_usd = s['credit_xof'] / rate
    n_usd = (s['credit_xof'] + s['debit_xof']) / rate
    cat_rows += f"""<tr class="drill-row" data-filter-type="category" data-filter-value="{cat}">
        <td data-sort="{cat}">{cat}</td>
        <td class="num" data-sort="{s['count']}">{s['count']:,}</td>
        <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
        <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
        <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
    </tr>"""

# Bank rows
bank_rows = ''
for bank, s in sorted(bank_stats.items(), key=lambda x: -x[1]['count']):
    d_usd = s['debit_xof'] / rate
    c_usd = s['credit_xof'] / rate
    n_usd = (s['credit_xof'] + s['debit_xof']) / rate
    bank_rows += f"""<tr class="drill-row" data-filter-type="bank" data-filter-value="{bank}">
        <td data-sort="{bdn(bank)}">{bdn(bank)}</td>
        <td class="num" data-sort="{s['count']}">{s['count']:,}</td>
        <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
        <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
        <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
    </tr>"""

# Account rows
acct_rows = ''
for acct, s in sorted(acct_stats.items(), key=lambda x: -x[1]['count']):
    d_usd = s['debit_xof'] / rate
    c_usd = s['credit_xof'] / rate
    n_usd = (s['credit_xof'] + s['debit_xof']) / rate
    acct_rows += f"""<tr class="drill-row" data-filter-type="account" data-filter-value="{acct}">
        <td data-sort="{acct}">{acct}</td>
        <td data-sort="{bdn(s['bank'])}">{bdn(s['bank'])}</td>
        <td class="num" data-sort="{s['count']}">{s['count']:,}</td>
        <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
        <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
        <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
    </tr>"""

# Flow rows
FLOW_ORDER = ['Collection', 'Payment', 'Inter-Account Transfer', 'Bank Costs', 'Payroll', 'Tax', 'Unclassified']
flow_rows = ''
for flow in FLOW_ORDER:
    if flow not in flow_stats:
        continue
    s = flow_stats[flow]
    d_usd = s['debit_xof'] / rate
    c_usd = s['credit_xof'] / rate
    n_usd = (s['credit_xof'] + s['debit_xof']) / rate
    flow_rows += f"""<tr class="drill-row" data-filter-type="flow" data-filter-value="{flow}">
        <td data-sort="{flow}" style="font-weight:600">{flow}</td>
        <td class="num" data-sort="{s['count']}">{s['count']:,}</td>
        <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
        <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
        <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
    </tr>"""

# Flow totals
flow_total_d = sum(s['debit_xof'] for s in flow_stats.values()) / rate
flow_total_c = sum(s['credit_xof'] for s in flow_stats.values()) / rate
flow_total_n = flow_total_c + flow_total_d

# Operational totals (excl IAT)
ops_flows = {k: v for k, v in flow_stats.items() if k != 'Inter-Account Transfer'}
ops_d = sum(s['debit_xof'] for s in ops_flows.values()) / rate
ops_c = sum(s['credit_xof'] for s in ops_flows.values()) / rate
ops_n = ops_c + ops_d

collection_stats = flow_stats.get('Collection', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
collection_credits_usd = collection_stats['credit_xof'] / rate
collection_count = collection_stats['count']
payment_stats = flow_stats.get('Payment', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
payment_debits_usd = payment_stats['debit_xof'] / rate
payment_count = payment_stats['count']
transfer_stats = flow_stats.get('Inter-Account Transfer', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
transfer_count = transfer_stats['count']
transfer_net = (transfer_stats['debit_xof'] + transfer_stats['credit_xof']) / rate

# Monthly rows
month_rows = ''
for month, s in sorted(month_stats.items()):
    d_usd = s['debit_xof'] / rate
    c_usd = s['credit_xof'] / rate
    n_usd = (s['credit_xof'] + s['debit_xof']) / rate
    month_rows += f"""<tr>
        <td data-sort="{month}">{month}</td>
        <td class="num" data-sort="{s['count']}">{s['count']:,}</td>
        <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
        <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
        <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
    </tr>"""

# Chart data
month_labels = json.dumps(sorted(month_stats.keys()))
month_debits_abs = json.dumps([round(abs(month_stats[m]['debit_xof']) / rate) for m in sorted(month_stats.keys())])
month_credits = json.dumps([round(month_stats[m]['credit_xof'] / rate) for m in sorted(month_stats.keys())])
month_net = json.dumps([round((month_stats[m]['credit_xof'] + month_stats[m]['debit_xof']) / rate) for m in sorted(month_stats.keys())])

cat_labels = json.dumps(list(sorted(cat_stats.keys(), key=lambda x: -cat_stats[x]['count'])))
cat_counts = json.dumps([cat_stats[c]['count'] for c in sorted(cat_stats.keys(), key=lambda x: -cat_stats[x]['count'])])

bk_labels = json.dumps([bdn(k) for k in sorted(bank_stats.keys(), key=lambda x: -bank_stats[x]['count'])])
bk_counts = json.dumps([bank_stats[k]['count'] for k in sorted(bank_stats.keys(), key=lambda x: -bank_stats[x]['count'])])

flow_labels = json.dumps([f for f in FLOW_ORDER if f in flow_stats])
flow_debits_usd = json.dumps([round(abs(flow_stats[f]['debit_xof']) / rate) for f in FLOW_ORDER if f in flow_stats])
flow_credits_usd = json.dumps([round(flow_stats[f]['credit_xof'] / rate) for f in FLOW_ORDER if f in flow_stats])

# Transfer route stats
route_stats = defaultdict(lambda: {'count': 0, 'total_xof': 0, 'total_usd': 0})
for t in transfers:
    route_key = (t['source_bank'], t['dest_bank'])
    route_stats[route_key]['count'] += 1
    route_stats[route_key]['total_xof'] += t['amount_xof']
    route_stats[route_key]['total_usd'] += t['amount_usd']

route_rows = ''
for (src_bank, dst_bank), rs in sorted(route_stats.items(), key=lambda x: -x[1]['total_usd']):
    avg_usd = rs['total_usd'] / rs['count'] if rs['count'] else 0
    route_rows += f"""<tr>
        <td data-sort="{bdn(src_bank)}">{bdn(src_bank)}</td>
        <td data-sort="{bdn(dst_bank)}">{bdn(dst_bank)}</td>
        <td class="num" data-sort="{rs['count']}">{rs['count']:,}</td>
        <td class="num" data-sort="{rs['total_usd']:.0f}">${rs['total_usd']:,.0f}</td>
        <td class="num" data-sort="{avg_usd:.0f}">${avg_usd:,.0f}</td>
    </tr>"""

transfer_total_usd = sum(t['amount_usd'] for t in transfers)
transfers_json = json.dumps(transfers)

# Date range
all_months = sorted(month_stats.keys())
min_month = all_months[0] if all_months else '2024-01'
max_month = all_months[-1] if all_months else '2025-12'

# Transaction JSON
txn_json = json.dumps(transactions)

# Fee metrics
total_fee_debit_xof = abs(cat_stats.get('Fees / Commissions', {}).get('debit_xof', 0)) + abs(cat_stats.get('Bank Charges', {}).get('debit_xof', 0))
total_payment_vol = abs(flow_stats.get('Payment', {}).get('debit_xof', 0))
fee_rate_pct = total_fee_debit_xof / total_payment_vol * 100 if total_payment_vol else 0
cheque_count = cat_stats.get('Check / Cheque', {}).get('count', 0)
cheque_pct = cheque_count / total_count * 100 if total_count else 0
swift_stats_val = cat_stats.get('SWIFT / Telex', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
swift_avg_usd = abs(swift_stats_val['debit_xof']) / swift_stats_val['count'] / rate if swift_stats_val['count'] else 0
low_activity_banks = [(bdn(b), s['count']) for b, s in bank_stats.items() if s['count'] < 1000]
low_activity_banks.sort(key=lambda x: x[1])
other_count = cat_stats.get('Other', {}).get('count', 0)
unclass_count = cat_stats.get('Unclassified', {}).get('count', 0)
opacity_pct = (other_count + unclass_count) / total_count * 100 if total_count else 0

consolidation_html = ''
for bname, cnt in low_activity_banks:
    color = '#c53030' if cnt < 100 else '#b7791f' if cnt < 500 else '#718096'
    consolidation_html += f'<tr><td>{bname}</td><td class="num" style="color:{color};font-weight:600">{cnt:,}</td></tr>'

# --- BUILD HTML ---
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GMA (Les Grands Moulins d'Abidjan) — XOF Transactions (USD)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
    --primary: #1a365d;
    --primary-light: #2c5282;
    --bg: #f7fafc;
    --card-bg: #ffffff;
    --text: #2d3748;
    --text-light: #718096;
    --border: #e2e8f0;
    --debit: #c53030;
    --credit: #276749;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:var(--bg); color:var(--text); font-size:14px; }}
.header {{ background:linear-gradient(135deg, var(--primary), var(--primary-light)); color:#fff; padding:24px 32px; }}
.header h1 {{ font-size:22px; font-weight:700; }}
.header .sub {{ font-size:13px; opacity:0.85; margin-top:4px; }}
.container {{ max-width:1400px; margin:0 auto; padding:20px; }}
.tabs {{ display:flex; gap:2px; background:var(--border); border-radius:8px 8px 0 0; padding:4px 4px 0; overflow-x:auto; }}
.tab {{ padding:10px 18px; cursor:pointer; background:#e2e8f0; border-radius:6px 6px 0 0; font-size:13px; font-weight:500; white-space:nowrap; border:none; color:var(--text); }}
.tab:hover {{ background:#cbd5e0; }}
.tab.active {{ background:var(--card-bg); color:var(--primary); font-weight:600; }}
.tab-content {{ display:none; padding:20px 0; }}
.tab-content.active {{ display:block; }}
.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px,1fr)); gap:16px; margin-bottom:24px; }}
.kpi {{ background:var(--card-bg); border-radius:8px; padding:18px; box-shadow:0 1px 3px rgba(0,0,0,0.08); text-align:center; }}
.kpi .label {{ font-size:11px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-light); margin-bottom:6px; }}
.kpi .value {{ font-size:24px; font-weight:700; color:var(--primary); }}
.kpi .sub {{ font-size:11px; color:var(--text-light); margin-top:4px; }}
.card {{ background:var(--card-bg); border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:20px; overflow:hidden; }}
.card-header {{ background:var(--bg); padding:12px 16px; font-weight:600; font-size:14px; border-bottom:1px solid var(--border); }}
.table-wrap {{ overflow-x:auto; }}
.scroll-table {{ max-height:500px; overflow-y:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:var(--primary); color:#fff; padding:10px 12px; text-align:left; position:sticky; top:0; z-index:1; cursor:pointer; white-space:nowrap; }}
th:hover {{ background:var(--primary-light); }}
td {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
tr:hover {{ background:#edf2f7; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.debit {{ color:var(--debit); }}
.credit {{ color:var(--credit); }}
.drill-row {{ cursor:pointer; }}
.drill-row:hover {{ background:#ebf4ff; }}
.chart-container {{ position:relative; height:350px; padding:16px; }}
.filter-bar {{ display:flex; gap:12px; align-items:center; margin-bottom:16px; flex-wrap:wrap; }}
.filter-bar input, .filter-bar select {{ padding:8px 12px; border:1px solid var(--border); border-radius:6px; font-size:13px; }}
.filter-bar input {{ min-width:220px; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }}
.badge-info {{ background:#ebf8ff; color:#2b6cb0; }}
tfoot td {{ font-weight:700; background:#f7fafc; border-top:2px solid var(--primary); }}
.back-btn {{ display:none; margin-bottom:12px; padding:6px 14px; background:var(--primary); color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:12px; }}
.back-btn:hover {{ background:var(--primary-light); }}
.empty-state {{ text-align:center; padding:60px 20px; color:var(--text-light); }}
.empty-state svg {{ width:48px; height:48px; margin-bottom:12px; opacity:0.4; }}
@media (max-width:768px) {{
    .kpi-row {{ grid-template-columns:1fr 1fr; }}
    .header {{ padding:16px; }}
    .container {{ padding:12px; }}
    .tab {{ padding:8px 12px; font-size:12px; }}
}}
</style>
</head>
<body>
<div class="header">
    <h1>GMA — Les Grands Moulins d'Abidjan</h1>
    <div class="sub">Ivory Coast | XOF Transactions in USD Equivalent | {min_month} to {max_month} | {total_count:,} transactions | 10 bank accounts</div>
</div>
<div class="container">
<div class="tabs">
    <button class="tab active" onclick="showTab('overview')">Overview</button>
    <button class="tab" onclick="showTab('cashflow')">Cash Flow</button>
    <button class="tab" onclick="showTab('types')">Types</button>
    <button class="tab" onclick="showTab('banks')">Banks</button>
    <button class="tab" onclick="showTab('accounts')">Accounts</button>
    <button class="tab" onclick="showTab('monthly')">Monthly</button>
    <button class="tab" onclick="showTab('transfers')">Transfers</button>
    <button class="tab" onclick="showTab('insights')">Insights</button>
    <button class="tab" onclick="showTab('transactions')">Transactions</button>
</div>

<!-- OVERVIEW -->
<div id="overview" class="tab-content active">
    <div class="kpi-row">
        <div class="kpi">
            <div class="label">Total Transactions</div>
            <div class="value">{total_count:,}</div>
            <div class="sub">{len(bank_stats)} banks &bull; 10 accounts</div>
        </div>
        <div class="kpi">
            <div class="label">Total Outflows (USD)</div>
            <div class="value debit">-${abs(total_debit_usd)/1e6:,.1f}M</div>
        </div>
        <div class="kpi">
            <div class="label">Total Inflows (USD)</div>
            <div class="value credit">+${total_credit_usd/1e6:,.1f}M</div>
        </div>
        <div class="kpi">
            <div class="label">Net Flow (USD)</div>
            <div class="value {'credit' if net_usd >= 0 else 'debit'}">{'+' if net_usd >= 0 else ''}${net_usd/1e6:,.1f}M</div>
        </div>
    </div>
    <div class="kpi-row">
        <div class="kpi">
            <div class="label">Collections</div>
            <div class="value credit">+${collection_credits_usd/1e6:,.1f}M</div>
            <div class="sub">{collection_count:,} txns</div>
        </div>
        <div class="kpi">
            <div class="label">Payments</div>
            <div class="value debit">-${abs(payment_debits_usd)/1e6:,.1f}M</div>
            <div class="sub">{payment_count:,} txns</div>
        </div>
        <div class="kpi">
            <div class="label">Operational Net</div>
            <div class="value {'credit' if ops_n >= 0 else 'debit'}">{'+' if ops_n >= 0 else ''}${ops_n/1e6:,.1f}M</div>
            <div class="sub">Excl. inter-account transfers</div>
        </div>
        <div class="kpi">
            <div class="label">Inter-Account Transfers</div>
            <div class="value">{transfer_count:,}</div>
            <div class="sub">Net imbalance: ${transfer_net:,.0f}</div>
        </div>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
        <div class="card">
            <div class="card-header">Flow Composition (USD)</div>
            <div class="chart-container"><canvas id="flowChart"></canvas></div>
        </div>
        <div class="card">
            <div class="card-header">Transaction Volume by Bank</div>
            <div class="chart-container"><canvas id="bankChart"></canvas></div>
        </div>
    </div>
</div>

<!-- CASH FLOW -->
<div id="cashflow" class="tab-content">
    <div class="card">
        <div class="card-header">Monthly Cash Flow (USD)</div>
        <div class="chart-container" style="height:400px;"><canvas id="monthlyChart"></canvas></div>
    </div>
    <div class="card">
        <div class="card-header">Cash Flow by Flow Type (USD)</div>
        <div class="table-wrap"><table>
            <thead><tr>
                <th class="sortable" data-col="0">Flow Type</th>
                <th class="sortable" data-col="1">Count</th>
                <th class="sortable" data-col="2">Outflows (USD)</th>
                <th class="sortable" data-col="3">Inflows (USD)</th>
                <th class="sortable" data-col="4">Net (USD)</th>
            </tr></thead>
            <tbody>{flow_rows}</tbody>
            <tfoot><tr>
                <td>Total</td>
                <td class="num">{total_count:,}</td>
                <td class="num debit">{flow_total_d:,.0f}</td>
                <td class="num credit">{flow_total_c:,.0f}</td>
                <td class="num {'credit' if flow_total_n >= 0 else 'debit'}">{fmt_net(flow_total_n)}</td>
            </tr></tfoot>
        </table></div>
    </div>
</div>

<!-- TYPES -->
<div id="types" class="tab-content">
    <button class="back-btn" id="typesBack" onclick="clearFilter()">&#8592; Back to all</button>
    <div class="card">
        <div class="card-header">Transaction Categories (USD)</div>
        <div class="table-wrap"><div class="scroll-table"><table>
            <thead><tr>
                <th class="sortable" data-col="0">Category</th>
                <th class="sortable" data-col="1">Count</th>
                <th class="sortable" data-col="2">Outflows (USD)</th>
                <th class="sortable" data-col="3">Inflows (USD)</th>
                <th class="sortable" data-col="4">Net (USD)</th>
            </tr></thead>
            <tbody>{cat_rows}</tbody>
        </table></div></div>
    </div>
    <div class="card">
        <div class="card-header">Category Distribution</div>
        <div class="chart-container"><canvas id="catChart"></canvas></div>
    </div>
</div>

<!-- BANKS -->
<div id="banks" class="tab-content">
    <button class="back-btn" id="banksBack" onclick="clearFilter()">&#8592; Back to all</button>
    <div class="card">
        <div class="card-header">Bank Summary (USD)</div>
        <div class="table-wrap"><div class="scroll-table"><table>
            <thead><tr>
                <th class="sortable" data-col="0">Bank</th>
                <th class="sortable" data-col="1">Count</th>
                <th class="sortable" data-col="2">Outflows (USD)</th>
                <th class="sortable" data-col="3">Inflows (USD)</th>
                <th class="sortable" data-col="4">Net (USD)</th>
            </tr></thead>
            <tbody>{bank_rows}</tbody>
        </table></div></div>
    </div>
</div>

<!-- ACCOUNTS -->
<div id="accounts" class="tab-content">
    <button class="back-btn" id="accountsBack" onclick="clearFilter()">&#8592; Back to all</button>
    <div class="card">
        <div class="card-header">Account Detail (USD)</div>
        <div class="table-wrap"><div class="scroll-table"><table>
            <thead><tr>
                <th class="sortable" data-col="0">Account</th>
                <th class="sortable" data-col="1">Bank</th>
                <th class="sortable" data-col="2">Count</th>
                <th class="sortable" data-col="3">Outflows (USD)</th>
                <th class="sortable" data-col="4">Inflows (USD)</th>
                <th class="sortable" data-col="5">Net (USD)</th>
            </tr></thead>
            <tbody>{acct_rows}</tbody>
        </table></div></div>
    </div>
</div>

<!-- MONTHLY -->
<div id="monthly" class="tab-content">
    <div class="card">
        <div class="card-header">Monthly Breakdown (USD)</div>
        <div class="table-wrap"><table>
            <thead><tr>
                <th class="sortable" data-col="0">Month</th>
                <th class="sortable" data-col="1">Count</th>
                <th class="sortable" data-col="2">Outflows (USD)</th>
                <th class="sortable" data-col="3">Inflows (USD)</th>
                <th class="sortable" data-col="4">Net (USD)</th>
            </tr></thead>
            <tbody>{month_rows}</tbody>
        </table></div>
    </div>
</div>

<!-- TRANSFERS -->
<div id="transfers" class="tab-content">
    <div class="kpi-row">
        <div class="kpi">
            <div class="label">Transfer Pairs</div>
            <div class="value">{len(transfers):,}</div>
        </div>
        <div class="kpi">
            <div class="label">Total Transferred (USD)</div>
            <div class="value">${transfer_total_usd:,.0f}</div>
        </div>
    </div>
    <div class="card">
        <div class="card-header">Transfer Routes</div>
        <div class="table-wrap"><table>
            <thead><tr>
                <th class="sortable" data-col="0">Source Bank</th>
                <th class="sortable" data-col="1">Dest Bank</th>
                <th class="sortable" data-col="2">Count</th>
                <th class="sortable" data-col="3">Total (USD)</th>
                <th class="sortable" data-col="4">Avg (USD)</th>
            </tr></thead>
            <tbody>{route_rows}</tbody>
        </table></div>
    </div>
    <div class="card">
        <div class="card-header">Transfer Detail</div>
        <div class="filter-bar">
            <input type="text" id="transferSearch" placeholder="Search transfers..." oninput="filterTransfers()">
        </div>
        <div class="table-wrap"><div class="scroll-table"><table>
            <thead><tr>
                <th>Date</th><th>Source Bank</th><th>Dest Bank</th><th>Amount (USD)</th><th>Description</th>
            </tr></thead>
            <tbody id="transferBody"></tbody>
        </table></div></div>
    </div>
</div>

<!-- INSIGHTS -->
<div id="insights" class="tab-content">
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:24px;">
        <div class="card" style="padding:20px;">
            <h3 style="color:var(--primary); margin-bottom:16px; font-size:16px;">Data Quality Metrics</h3>
            <table style="width:100%;font-size:13px;">
                <tr><td>Unclassified Rate</td><td class="num" style="font-weight:600;">{unclass_count/total_count*100:.1f}%</td><td style="font-size:11px;color:var(--text-light)">Target: &lt;5%</td></tr>
                <tr><td>"Other" Rate</td><td class="num" style="font-weight:600;">{other_count/total_count*100:.1f}%</td><td style="font-size:11px;color:var(--text-light)">Target: &lt;10%</td></tr>
                <tr><td>Combined Opacity</td><td class="num" style="font-weight:600;color:{'#c53030' if opacity_pct > 15 else '#276749'}">{opacity_pct:.1f}%</td><td style="font-size:11px;color:var(--text-light)">Target: &lt;15%</td></tr>
                <tr><td>Low-Activity Banks (&lt;1K txns)</td><td class="num" style="font-weight:600;">{len(low_activity_banks)}</td><td style="font-size:11px;color:var(--text-light)">Consolidation candidates</td></tr>
            </table>
        </div>
        <div class="card" style="padding:20px;">
            <h3 style="color:var(--primary); margin-bottom:16px; font-size:16px;">Operational Indicators</h3>
            <table style="width:100%;font-size:13px;">
                <tr><td>Fee/Commission Rate</td><td class="num" style="font-weight:600;color:{'#c53030' if fee_rate_pct > 1.5 else '#276749'}">{fee_rate_pct:.2f}%</td><td style="font-size:11px;color:var(--text-light)">of payment volume</td></tr>
                <tr><td>Cheque Volume</td><td class="num" style="font-weight:600;">{cheque_pct:.1f}%</td><td style="font-size:11px;color:var(--text-light)">{cheque_count:,} txns</td></tr>
                <tr><td>SWIFT/Telex Avg Value</td><td class="num" style="font-weight:600;">${swift_avg_usd:,.0f}</td><td style="font-size:11px;color:var(--text-light)">{swift_stats_val['count']} txns</td></tr>
                <tr><td>IAT Net Imbalance</td><td class="num" style="font-weight:600;color:#b7791f">${transfer_net:,.0f}</td><td style="font-size:11px;color:var(--text-light)">Should be ~$0</td></tr>
            </table>
        </div>
    </div>
    {"<div class='card' style='margin-bottom:20px;'><div class='card-header'>Bank Consolidation Candidates (&lt;1,000 transactions)</div><div class='table-wrap'><table><thead><tr><th>Bank</th><th>Transaction Count</th></tr></thead><tbody>" + consolidation_html + "</tbody></table></div></div>" if consolidation_html else ""}
</div>

<!-- TRANSACTIONS -->
<div id="transactions" class="tab-content">
    <div class="filter-bar">
        <input type="text" id="txnSearch" placeholder="Search description, bank, account, ref..." oninput="filterTxns()">
        <select id="txnBank" onchange="filterTxns()"><option value="">All Banks</option></select>
        <select id="txnCat" onchange="filterTxns()"><option value="">All Categories</option></select>
        <select id="txnFlow" onchange="filterTxns()"><option value="">All Flows</option></select>
        <input type="month" id="txnFrom" onchange="filterTxns()" value="{min_month}">
        <span>to</span>
        <input type="month" id="txnTo" onchange="filterTxns()" value="{max_month}">
        <span id="txnCount" style="font-size:12px;color:var(--text-light);"></span>
    </div>
    <div class="card">
        <div class="table-wrap"><div class="scroll-table" style="max-height:600px;">
            <table>
                <thead><tr>
                    <th class="sortable" data-col="0">Date</th>
                    <th class="sortable" data-col="1">Bank</th>
                    <th class="sortable" data-col="2">Account</th>
                    <th class="sortable" data-col="3">Category</th>
                    <th class="sortable" data-col="4">Flow</th>
                    <th class="sortable" data-col="5">Amount (USD)</th>
                    <th class="sortable" data-col="6">Amount (XOF)</th>
                    <th class="sortable" data-col="7">Description</th>
                    <th class="sortable" data-col="8">Ref</th>
                </tr></thead>
                <tbody id="txnBody"></tbody>
            </table>
        </div></div>
    </div>
</div>
</div>

<script>
const BANK_DISPLAY = {json.dumps(BANK_DISPLAY)};
function bdn(n) {{ return BANK_DISPLAY[n] || n; }}

const allTxns = {txn_json};
const allTransfers = {transfers_json};
let filteredTxns = allTxns;
const PAGE_SIZE = 500;

function showTab(id) {{
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
    if (id === 'transactions' && !document.getElementById('txnBody').innerHTML) initTxns();
    if (id === 'transfers' && !document.getElementById('transferBody').innerHTML) renderTransfers(allTransfers);
}}

// Sorting
document.querySelectorAll('.sortable').forEach(th => {{
    th.addEventListener('click', function() {{
        const table = this.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const col = parseInt(this.dataset.col);
        const asc = this.dataset.asc !== 'true';
        this.dataset.asc = asc;
        rows.sort((a, b) => {{
            const av = a.cells[col]?.dataset.sort || a.cells[col]?.textContent || '';
            const bv = b.cells[col]?.dataset.sort || b.cells[col]?.textContent || '';
            const an = parseFloat(av), bn = parseFloat(bv);
            if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
            return asc ? av.localeCompare(bv) : bv.localeCompare(av);
        }});
        rows.forEach(r => tbody.appendChild(r));
    }});
}});

// Drill-down
document.querySelectorAll('.drill-row').forEach(row => {{
    row.addEventListener('click', function() {{
        const type = this.dataset.filterType;
        const value = this.dataset.filterValue;
        showTab('transactions');
        document.querySelectorAll('.tab').forEach(t => {{ if(t.textContent==='Transactions') t.classList.add('active'); else t.classList.remove('active'); }});
        if (type === 'bank') document.getElementById('txnBank').value = value;
        else if (type === 'category') document.getElementById('txnCat').value = value;
        else if (type === 'flow') document.getElementById('txnFlow').value = value;
        else if (type === 'account') {{
            document.getElementById('txnSearch').value = value;
        }}
        filterTxns();
    }});
}});

function initTxns() {{
    const bankSel = document.getElementById('txnBank');
    const catSel = document.getElementById('txnCat');
    const flowSel = document.getElementById('txnFlow');
    const banks = [...new Set(allTxns.map(t => t.bank))].sort();
    const cats = [...new Set(allTxns.map(t => t.category))].sort();
    const flows = [...new Set(allTxns.map(t => t.flow_type))].sort();
    banks.forEach(b => {{ const o = document.createElement('option'); o.value = b; o.textContent = bdn(b); bankSel.appendChild(o); }});
    cats.forEach(c => {{ const o = document.createElement('option'); o.value = c; o.textContent = c; catSel.appendChild(o); }});
    flows.forEach(f => {{ const o = document.createElement('option'); o.value = f; o.textContent = f; flowSel.appendChild(o); }});
    filterTxns();
}}

function filterTxns() {{
    const search = (document.getElementById('txnSearch').value || '').toLowerCase();
    const bank = document.getElementById('txnBank').value;
    const cat = document.getElementById('txnCat').value;
    const flow = document.getElementById('txnFlow').value;
    const from = document.getElementById('txnFrom').value;
    const to = document.getElementById('txnTo').value;

    filteredTxns = allTxns.filter(t => {{
        if (bank && t.bank !== bank) return false;
        if (cat && t.category !== cat) return false;
        if (flow && t.flow_type !== flow) return false;
        if (from && t.month < from) return false;
        if (to && t.month > to) return false;
        if (search && !(t.description||'').toLowerCase().includes(search) && !(t.bank||'').toLowerCase().includes(search)
            && !(t.account||'').toLowerCase().includes(search) && !(t.ref||'').toLowerCase().includes(search)
            && !(t.beneficiary||'').toLowerCase().includes(search)) return false;
        return true;
    }});

    document.getElementById('txnCount').textContent = filteredTxns.length.toLocaleString() + ' transactions';
    renderTxnPage(filteredTxns.slice(0, PAGE_SIZE));
}}

function renderTxnPage(txns) {{
    const tbody = document.getElementById('txnBody');
    tbody.innerHTML = txns.map(t => `<tr>
        <td data-sort="${{t.date}}">${{t.date}}</td>
        <td data-sort="${{t.bank}}">${{bdn(t.bank)}}</td>
        <td data-sort="${{t.account}}">${{t.account}}</td>
        <td data-sort="${{t.category}}">${{t.category}}</td>
        <td data-sort="${{t.flow_type}}">${{t.flow_type}}</td>
        <td class="num ${{t.amount_usd >= 0 ? 'credit' : 'debit'}}" data-sort="${{t.amount_usd}}">${{t.amount_usd.toLocaleString('en-US', {{minimumFractionDigits:0, maximumFractionDigits:0}})}}</td>
        <td class="num ${{t.amount_xof >= 0 ? 'credit' : 'debit'}}" data-sort="${{t.amount_xof}}">${{t.amount_xof.toLocaleString('en-US', {{minimumFractionDigits:0, maximumFractionDigits:0}})}}</td>
        <td>${{t.description || ''}}</td>
        <td>${{t.ref || ''}}</td>
    </tr>`).join('');
    if (filteredTxns.length > PAGE_SIZE) {{
        tbody.innerHTML += `<tr><td colspan="9" style="text-align:center;padding:16px;color:var(--text-light);">Showing ${{PAGE_SIZE}} of ${{filteredTxns.length.toLocaleString()}} — use filters to narrow</td></tr>`;
    }}
}}

function clearFilter() {{
    document.getElementById('txnSearch').value = '';
    document.getElementById('txnBank').value = '';
    document.getElementById('txnCat').value = '';
    document.getElementById('txnFlow').value = '';
    filterTxns();
}}

function renderTransfers(list) {{
    const tbody = document.getElementById('transferBody');
    const show = list.slice(0, 500);
    tbody.innerHTML = show.map(t => `<tr>
        <td>${{t.date}}</td>
        <td>${{bdn(t.source_bank)}}</td>
        <td>${{bdn(t.dest_bank)}}</td>
        <td class="num">${{t.amount_usd.toLocaleString('en-US', {{style:'currency',currency:'USD',minimumFractionDigits:0}})}}</td>
        <td>${{t.description || ''}}</td>
    </tr>`).join('');
}}

function filterTransfers() {{
    const search = (document.getElementById('transferSearch').value || '').toLowerCase();
    const filtered = allTransfers.filter(t => {{
        if (!search) return true;
        return (t.source_bank||'').toLowerCase().includes(search) || (t.dest_bank||'').toLowerCase().includes(search)
            || (t.description||'').toLowerCase().includes(search);
    }});
    renderTransfers(filtered);
}}

// Charts
window.addEventListener('DOMContentLoaded', () => {{
    // Flow chart
    new Chart(document.getElementById('flowChart'), {{
        type: 'bar',
        data: {{
            labels: {flow_labels},
            datasets: [
                {{ label: 'Outflows (USD)', data: {flow_debits_usd}, backgroundColor: 'rgba(197,48,48,0.7)' }},
                {{ label: 'Inflows (USD)', data: {flow_credits_usd}, backgroundColor: 'rgba(39,103,73,0.7)' }}
            ]
        }},
        options: {{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'bottom'}}}},
            scales:{{ y:{{ ticks:{{ callback: v => '$'+v.toLocaleString() }} }} }} }}
    }});

    // Bank chart
    new Chart(document.getElementById('bankChart'), {{
        type: 'bar',
        data: {{
            labels: {bk_labels},
            datasets: [{{ label: 'Transactions', data: {bk_counts}, backgroundColor: 'rgba(26,54,93,0.7)' }}]
        }},
        options: {{ responsive:true, maintainAspectRatio:false, indexAxis:'y', plugins:{{legend:{{display:false}}}},
            scales:{{ x:{{ ticks:{{ callback: v => v.toLocaleString() }} }} }} }}
    }});

    // Monthly chart
    new Chart(document.getElementById('monthlyChart'), {{
        type: 'bar',
        data: {{
            labels: {month_labels},
            datasets: [
                {{ label: 'Outflows', data: {month_debits_abs}, backgroundColor: 'rgba(197,48,48,0.6)' }},
                {{ label: 'Inflows', data: {month_credits}, backgroundColor: 'rgba(39,103,73,0.6)' }},
                {{ label: 'Net', data: {month_net}, type:'line', borderColor:'#2b6cb0', backgroundColor:'transparent', tension:0.3, pointRadius:3 }}
            ]
        }},
        options: {{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'bottom'}}}},
            scales:{{ y:{{ ticks:{{ callback: v => '$'+v.toLocaleString() }} }} }} }}
    }});

    // Category chart
    new Chart(document.getElementById('catChart'), {{
        type: 'doughnut',
        data: {{
            labels: {cat_labels},
            datasets: [{{ data: {cat_counts}, backgroundColor: ['#1a365d','#2c5282','#2b6cb0','#3182ce','#4299e1','#63b3ed','#90cdf4','#bee3f8','#c53030','#e53e3e','#fc8181','#feb2b2','#276749','#38a169','#68d391'] }}]
        }},
        options: {{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'right',labels:{{font:{{size:11}}}}}}}} }}
    }});
}});
</script>
</body>
</html>"""

with open('ctm-gma-transactions.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Generated ctm-gma-transactions.html')
print(f'  Transactions: {total_count:,}')
print(f'  Banks: {len(bank_stats)}')
print(f'  Accounts: {len(acct_stats)}')
print(f'  Date range: {min_month} to {max_month}')
print(f'  Transfers: {len(transfers)}')
