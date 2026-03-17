import json, sys
from datetime import datetime
from collections import defaultdict

# --gma flag: filter to Ivory Coast (GMA) only
GMA_MODE = '--gma' in sys.argv
FILTER_COUNTRY = 'Ivory Coast' if GMA_MODE else None
REPORT_TITLE = 'GMA — XOF Transaction Analysis' if GMA_MODE else 'CTM Division - XOF Transaction Analysis'
REPORT_SUBTITLE_REGION = 'Ivory Coast (GMA)' if GMA_MODE else 'West Africa (Ivory Coast & Senegal)'
OUTPUT_FILE = 'gma-transactions.html' if GMA_MODE else 'ctm-xof-transactions-usd.html'
CSV_FILENAME = 'gma_xof_transactions_usd.csv' if GMA_MODE else 'ctm_xof_transactions_usd.csv'
PAGE_TITLE = 'GMA - XOF Transactions (USD Converted)' if GMA_MODE else 'CTM Division - XOF Transactions (USD Converted)'

with open('ctm_data.json', 'r') as f:
    data = json.load(f)

rate = data['rate']
transactions = data['transactions']
transfers = data.get('transfers', [])

# Filter if GMA mode
if FILTER_COUNTRY:
    transactions = [t for t in transactions if t.get('country') == FILTER_COUNTRY]
    transfers = [t for t in transfers if t.get('source_country') == FILTER_COUNTRY or t.get('dest_country') == FILTER_COUNTRY]

    # Recalculate all stats from filtered transactions
    cat_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
    bank_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
    month_stats = {}  # ordered dict by month
    country_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0, 'banks': set()})
    flow_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})

    month_keys = sorted(set(t['month'] for t in transactions))
    for mk in month_keys:
        month_stats[mk] = {'count': 0, 'debit_xof': 0, 'credit_xof': 0}

    for t in transactions:
        cat = t['category']
        bank = t['bank']
        month = t['month']
        country = t['country']
        flow = t['flow_type']
        amt = t['amount_xof']

        for stats, key in [(cat_stats, cat), (bank_stats, bank), (flow_stats, flow)]:
            stats[key]['count'] += 1
            if amt < 0:
                stats[key]['debit_xof'] += amt
            else:
                stats[key]['credit_xof'] += amt

        month_stats[month]['count'] += 1
        if amt < 0:
            month_stats[month]['debit_xof'] += amt
        else:
            month_stats[month]['credit_xof'] += amt

        country_stats[country]['count'] += 1
        country_stats[country]['banks'].add(bank)
        if amt < 0:
            country_stats[country]['debit_xof'] += amt
        else:
            country_stats[country]['credit_xof'] += amt

    # Convert sets to lists for JSON compatibility
    cat_stats = dict(cat_stats)
    bank_stats = dict(bank_stats)
    flow_stats = dict(flow_stats)
    for cs in country_stats.values():
        cs['banks'] = list(cs['banks'])
    country_stats = dict(country_stats)

    data['total_count'] = len(transactions)
    data['transactions'] = transactions
    print(f'GMA mode: filtered to {FILTER_COUNTRY} — {len(transactions):,} transactions, {len(transfers):,} transfers')
else:
    cat_stats = data['category_stats']
    bank_stats = data['bank_stats']
    month_stats = data['month_stats']
    country_stats = data['country_stats']
    flow_stats = data['flow_stats']

# H-05: Bank display name normalization
BANK_DISPLAY = {
    'AFG BK': 'AFG Bank (Africa Financial Group)',
    'BANQUE POPULAIRE': 'Banque Populaire CI',
    'BICIS Senegal': 'BICIS Senegal',
    'Bank Atlantique SN': 'Banque Atlantique Senegal',
    'Bank Atlantique IC': 'Banque Atlantique Ivory Coast',
    'C.B.A.O. Senegal': 'CBAO Senegal',
    'BOA Ivory Coast': 'BOA Ivory Coast',
    'Bank Africa Senegal': 'Bank of Africa Senegal',
    'SOCGEN Ivory Coast': 'Societe Generale Ivory Coast',
    'SOCGEN SENEGAL BNK': 'Societe Generale Senegal',
    'SIB (IVORIAN BANK)': 'SIB (Societe Ivoirienne de Banque)',
    'MTN Mobile FS CI': 'MTN Mobile Money CI',
    'Citi Senegal Bank': 'Citibank Senegal',
    'CITI IVORY COAST': 'Citibank Ivory Coast',
    'STANBIC IVORY COAST': 'Stanbic Bank Ivory Coast',
}

def bdn(name):
    return BANK_DISPLAY.get(name, name)

# Compute totals
total_debit_xof = sum(s['debit_xof'] for s in cat_stats.values())
total_credit_xof = sum(s['credit_xof'] for s in cat_stats.values())
total_debit_usd = total_debit_xof / rate
total_credit_usd = total_credit_xof / rate
net_xof = total_credit_xof + total_debit_xof
net_usd = net_xof / rate

def fmt_net(val):
    """C-03: Add +/- prefix to net values for accessibility"""
    if val >= 0:
        return f'+{val:,.0f}'
    else:
        return f'{val:,.0f}'

# Build category rows — C-01: add data-sort attrs for sorting
cat_rows = ''
for cat, s in cat_stats.items():
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

# Build bank-to-country mapping
bank_to_country = {}
for country, cs in country_stats.items():
    for b in cs['banks']:
        bank_to_country[b] = country

# Build bank rows with country column
bank_rows = ''
for bank, s in bank_stats.items():
    d_usd = s['debit_xof'] / rate
    c_usd = s['credit_xof'] / rate
    n_usd = (s['credit_xof'] + s['debit_xof']) / rate
    country = bank_to_country.get(bank, 'Unknown')
    bank_rows += f"""<tr class="drill-row" data-filter-type="bank" data-filter-value="{bank}">
        <td data-sort="{bdn(bank)}">{bdn(bank)}</td>
        <td data-sort="{country}">{country}</td>
        <td class="num" data-sort="{s['count']}">{s['count']:,}</td>
        <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
        <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
        <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
    </tr>"""

# Build country rows
country_rows = ''
for country, s in country_stats.items():
    d_usd = s['debit_xof'] / rate
    c_usd = s['credit_xof'] / rate
    n_usd = (s['credit_xof'] + s['debit_xof']) / rate
    country_rows += f"""<tr class="drill-row" data-filter-type="country" data-filter-value="{country}">
        <td style="font-weight:600" data-sort="{country}">{country}</td>
        <td class="num" data-sort="{len(s['banks'])}">{len(s['banks'])}</td>
        <td class="num" data-sort="{s['count']}">{s['count']:,}</td>
        <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
        <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
        <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
    </tr>"""

# Build country-bank detail rows
country_bank_rows = ''
for country, s in country_stats.items():
    for bk in s['banks']:
        bs = bank_stats[bk]
        d_usd = bs['debit_xof'] / rate
        c_usd = bs['credit_xof'] / rate
        n_usd = (bs['credit_xof'] + bs['debit_xof']) / rate
        country_bank_rows += f"""<tr class="drill-row" data-filter-type="bank" data-filter-value="{bk}">
            <td data-sort="{country}">{country}</td>
            <td data-sort="{bdn(bk)}">{bdn(bk)}</td>
            <td class="num" data-sort="{bs['count']}">{bs['count']:,}</td>
            <td class="num debit" data-sort="{d_usd:.0f}">{d_usd:,.0f}</td>
            <td class="num credit" data-sort="{c_usd:.0f}">{c_usd:,.0f}</td>
            <td class="num {'credit' if n_usd >= 0 else 'debit'}" data-sort="{n_usd:.0f}">{fmt_net(n_usd)}</td>
        </tr>"""

# Build flow type rows
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

# Flow totals for footer
flow_total_d = sum(s['debit_xof'] for s in flow_stats.values()) / rate
flow_total_c = sum(s['credit_xof'] for s in flow_stats.values()) / rate
flow_total_n = flow_total_c + flow_total_d

# Compute "operational" totals (excluding inter-account transfers)
ops_flows = {k: v for k, v in flow_stats.items() if k != 'Inter-Account Transfer'}
ops_d = sum(s['debit_xof'] for s in ops_flows.values()) / rate
ops_c = sum(s['credit_xof'] for s in ops_flows.values()) / rate
ops_n = ops_c + ops_d
transfer_stats = flow_stats.get('Inter-Account Transfer', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
transfer_count = transfer_stats['count']
transfer_net = (transfer_stats['debit_xof'] + transfer_stats['credit_xof']) / rate

collection_stats = flow_stats.get('Collection', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
collection_credits_usd = collection_stats['credit_xof'] / rate
collection_count = collection_stats['count']
payment_stats = flow_stats.get('Payment', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
payment_debits_usd = payment_stats['debit_xof'] / rate
payment_count = payment_stats['count']

# Flow chart data
flow_labels = json.dumps([f for f in FLOW_ORDER if f in flow_stats])
flow_debits_usd = json.dumps([round(abs(flow_stats[f]['debit_xof']) / rate) for f in FLOW_ORDER if f in flow_stats])
flow_credits_usd = json.dumps([round(flow_stats[f]['credit_xof'] / rate) for f in FLOW_ORDER if f in flow_stats])
flow_counts = json.dumps([flow_stats[f]['count'] for f in FLOW_ORDER if f in flow_stats])

# Country chart data
country_labels = json.dumps(list(country_stats.keys()))
country_counts = json.dumps([s['count'] for s in country_stats.values()])
country_debits_usd = json.dumps([round(abs(s['debit_xof']) / rate) for s in country_stats.values()])
country_credits_usd = json.dumps([round(s['credit_xof'] / rate) for s in country_stats.values()])

# Build monthly rows
month_rows = ''
for month, s in month_stats.items():
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

# Monthly chart data — H-01: use absolute values for debits
month_labels = json.dumps(list(month_stats.keys()))
month_debits_abs = json.dumps([round(abs(s['debit_xof']) / rate) for s in month_stats.values()])
month_credits = json.dumps([round(s['credit_xof'] / rate) for s in month_stats.values()])
month_net = json.dumps([round((s['credit_xof'] + s['debit_xof']) / rate) for s in month_stats.values()])

# Category chart data
cat_labels = json.dumps(list(cat_stats.keys()))
cat_counts = json.dumps([s['count'] for s in cat_stats.values()])

# Bank chart data — H-05: use display names
bk_labels = json.dumps([bdn(k) for k in bank_stats.keys()])
bk_counts = json.dumps([s['count'] for s in bank_stats.values()])

# Build transfers tab data
transfer_total_usd = sum(t['amount_usd'] for t in transfers)
transfer_total_xof = sum(t['amount_xof'] for t in transfers)

# Transfers: aggregate by route (source_bank -> dest_bank)
route_stats = defaultdict(lambda: {'count': 0, 'total_xof': 0, 'total_usd': 0})
for t in transfers:
    route_key = (t['source_bank'], t['dest_bank'])
    route_stats[route_key]['count'] += 1
    route_stats[route_key]['total_xof'] += t['amount_xof']
    route_stats[route_key]['total_usd'] += t['amount_usd']

# Build route summary rows
route_rows = ''
for (src_bank, dst_bank), rs in sorted(route_stats.items(), key=lambda x: -x[1]['total_usd']):
    src_country = bank_to_country.get(src_bank, 'Unknown')
    dst_country = bank_to_country.get(dst_bank, 'Unknown')
    avg_usd = rs['total_usd'] / rs['count'] if rs['count'] else 0
    route_rows += f"""<tr>
        <td data-sort="{bdn(src_bank)}">{bdn(src_bank)}</td>
        <td data-sort="{src_country}">{src_country}</td>
        <td data-sort="{bdn(dst_bank)}">{bdn(dst_bank)}</td>
        <td data-sort="{dst_country}">{dst_country}</td>
        <td class="num" data-sort="{rs['count']}">{rs['count']:,}</td>
        <td class="num" data-sort="{rs['total_usd']:.0f}">${rs['total_usd']:,.0f}</td>
        <td class="num" data-sort="{avg_usd:.0f}">${avg_usd:,.0f}</td>
    </tr>"""

# Enrich transfers with debit/credit dates, float days, and both-side details
# Use ALL transactions for ref lookup (not filtered), so cross-entity refs resolve
all_txns_for_ref = data.get('_all_transactions', transactions)
if FILTER_COUNTRY:
    # Reload full transaction list for ref resolution
    with open('ctm_data.json', 'r') as _f:
        _full = json.load(_f)
    all_txns_for_ref = _full['transactions']

ref_to_txn = {}
for t in all_txns_for_ref:
    ref = t.get('ref')
    if ref:
        ref_to_txn[ref] = t

for tr in transfers:
    debit_txn = ref_to_txn.get(tr.get('debit_ref'), {})
    credit_txn = ref_to_txn.get(tr.get('credit_ref'), {})
    # PostedDate (booking date)
    tr['debit_date'] = debit_txn.get('date', '')
    tr['credit_date'] = credit_txn.get('date', '')
    # ValueDate (bank value date)
    tr['debit_value_date'] = debit_txn.get('value_date', '')
    tr['credit_value_date'] = credit_txn.get('value_date', '')
    tr['debit_desc'] = debit_txn.get('description', '')
    tr['credit_desc'] = credit_txn.get('description', '')
    tr['debit_category'] = debit_txn.get('category', '')
    tr['credit_category'] = credit_txn.get('category', '')
    # Float on PostedDate
    if tr['debit_date'] and tr['credit_date']:
        dd = datetime.strptime(tr['debit_date'], '%Y-%m-%d')
        cd = datetime.strptime(tr['credit_date'], '%Y-%m-%d')
        tr['float_days'] = (cd - dd).days
    else:
        tr['float_days'] = None
    # Float on ValueDate
    if tr['debit_value_date'] and tr['credit_value_date']:
        try:
            dvd = datetime.strptime(tr['debit_value_date'], '%Y-%m-%d')
            cvd = datetime.strptime(tr['credit_value_date'], '%Y-%m-%d')
            tr['value_float_days'] = (cvd - dvd).days
        except:
            tr['value_float_days'] = None
    else:
        tr['value_float_days'] = None

# Split transfers: intra-entity vs intercompany
intra_transfers = [t for t in transfers if t['source_country'] == t['dest_country']]
ic_transfers = [t for t in transfers if t['source_country'] != t['dest_country']]

# Float stats (all) — PostedDate
float_values = [tr['float_days'] for tr in transfers if tr['float_days'] is not None]
avg_float = sum(float_values) / len(float_values) if float_values else 0
max_float = max(float_values) if float_values else 0
zero_float = sum(1 for f in float_values if f == 0)
positive_float = sum(1 for f in float_values if f and f > 0)

# Float stats (all) — ValueDate
vfloat_values = [tr['value_float_days'] for tr in transfers if tr['value_float_days'] is not None]
avg_vfloat = sum(vfloat_values) / len(vfloat_values) if vfloat_values else 0
max_vfloat = max(vfloat_values) if vfloat_values else 0

# Intra-entity float stats
intra_float = [tr['float_days'] for tr in intra_transfers if tr['float_days'] is not None]
intra_avg_float = sum(intra_float) / len(intra_float) if intra_float else 0
intra_max_float = max(intra_float) if intra_float else 0
intra_zero_float = sum(1 for f in intra_float if f == 0)
intra_total_usd = sum(t['amount_usd'] for t in intra_transfers)
intra_vfloat = [tr['value_float_days'] for tr in intra_transfers if tr['value_float_days'] is not None]
intra_avg_vfloat = sum(intra_vfloat) / len(intra_vfloat) if intra_vfloat else 0

# Intercompany float stats
ic_float = [tr['float_days'] for tr in ic_transfers if tr['float_days'] is not None]
ic_avg_float = sum(ic_float) / len(ic_float) if ic_float else 0
ic_max_float = max(ic_float) if ic_float else 0
ic_zero_float = sum(1 for f in ic_float if f == 0)
ic_total_usd = sum(t['amount_usd'] for t in ic_transfers)
ic_vfloat = [tr['value_float_days'] for tr in ic_transfers if tr['value_float_days'] is not None]
ic_avg_vfloat = sum(ic_vfloat) / len(ic_vfloat) if ic_vfloat else 0

# JSON for client-side rendering
intra_transfers_json = json.dumps(intra_transfers)
ic_transfers_json = json.dumps(ic_transfers)
transfers_json = json.dumps(transfers)

# Legacy stats for other sections
cross_border_count = len(ic_transfers)
intra_country_count = len(intra_transfers)
cross_border_usd = ic_total_usd
intra_country_usd = intra_total_usd

# Per-country detailed stats for Country Review tab
country_detail = {}
for country_name, cs in country_stats.items():
    # Per-country category breakdown
    c_cat = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
    c_flow = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
    c_monthly = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
    c_bank = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
    for t in transactions:
        if t['country'] != country_name:
            continue
        for stats, key in [(c_cat, t['category']), (c_flow, t['flow_type']), (c_monthly, t['month']), (c_bank, t['bank'])]:
            stats[key]['count'] += 1
            if t['amount_xof'] < 0:
                stats[key]['debit_xof'] += t['amount_xof']
            else:
                stats[key]['credit_xof'] += t['amount_xof']
    country_detail[country_name] = {
        'cat': dict(c_cat),
        'flow': dict(c_flow),
        'monthly': dict(c_monthly),
        'bank': dict(c_bank),
        'total_count': cs['count'],
        'total_debit_xof': cs['debit_xof'],
        'total_credit_xof': cs['credit_xof'],
    }

# Build Country Review HTML sections
country_review_html = ''
for country_name in sorted(country_stats.keys()):
    cd = country_detail[country_name]
    td_usd = cd['total_debit_xof'] / rate
    tc_usd = cd['total_credit_xof'] / rate
    tn_usd = (cd['total_credit_xof'] + cd['total_debit_xof']) / rate

    # KPI row
    country_review_html += f"""
    <h3 style="font-size:18px; margin:24px 0 12px; padding-bottom:8px; border-bottom:2px solid var(--primary); color:var(--primary);">{country_name}</h3>
    <div class="kpi-row">
        <div class="kpi">
            <div class="label">Transactions</div>
            <div class="value">{cd['total_count']:,}</div>
            <div class="sub">{len(cd['bank']):,} banks</div>
        </div>
        <div class="kpi">
            <div class="label">Outflows (USD)</div>
            <div class="value debit">-${abs(td_usd)/1e6:,.1f}M</div>
        </div>
        <div class="kpi">
            <div class="label">Inflows (USD)</div>
            <div class="value credit">+${tc_usd/1e6:,.1f}M</div>
        </div>
        <div class="kpi">
            <div class="label">Net (USD)</div>
            <div class="value {'credit' if tn_usd >= 0 else 'debit'}">{'+' if tn_usd >= 0 else ''}${tn_usd/1e6:,.1f}M</div>
        </div>
    </div>"""

    # Bank breakdown table
    country_review_html += """<div class="card"><div class="card-header">Bank Breakdown (USD)</div><div class="table-wrap"><div class="scroll-table"><table>
    <thead><tr><th class="sortable" data-col="0">Bank</th><th class="sortable" data-col="1">Count</th>
    <th class="sortable" data-col="2">Outflows (USD)</th><th class="sortable" data-col="3">Inflows (USD)</th>
    <th class="sortable" data-col="4">Net (USD)</th><th class="sortable" data-col="5">% of Country Vol</th></tr></thead><tbody>"""
    total_vol = abs(cd['total_debit_xof']) + cd['total_credit_xof']
    for bk, bs in sorted(cd['bank'].items(), key=lambda x: -x[1]['count']):
        d = bs['debit_xof'] / rate
        c = bs['credit_xof'] / rate
        n = (bs['credit_xof'] + bs['debit_xof']) / rate
        vol = abs(bs['debit_xof']) + bs['credit_xof']
        pct = vol / total_vol * 100 if total_vol else 0
        country_review_html += f"""<tr class="drill-row" data-filter-type="bank" data-filter-value="{bk}">
            <td data-sort="{bdn(bk)}">{bdn(bk)}</td>
            <td class="num" data-sort="{bs['count']}">{bs['count']:,}</td>
            <td class="num debit" data-sort="{d:.0f}">{d:,.0f}</td>
            <td class="num credit" data-sort="{c:.0f}">{c:,.0f}</td>
            <td class="num {'credit' if n >= 0 else 'debit'}" data-sort="{n:.0f}">{fmt_net(n)}</td>
            <td class="num" data-sort="{pct:.1f}">{pct:.1f}%</td>
        </tr>"""
    country_review_html += "</tbody></table></div></div></div>"

    # Flow type table
    country_review_html += """<div class="card"><div class="card-header">Flow Type Breakdown (USD)</div><div class="table-wrap"><table>
    <thead><tr><th class="sortable" data-col="0">Flow Type</th><th class="sortable" data-col="1">Count</th>
    <th class="sortable" data-col="2">Outflows (USD)</th><th class="sortable" data-col="3">Inflows (USD)</th>
    <th class="sortable" data-col="4">Net (USD)</th></tr></thead><tbody>"""
    for flow in FLOW_ORDER:
        if flow not in cd['flow']:
            continue
        fs = cd['flow'][flow]
        d = fs['debit_xof'] / rate
        c = fs['credit_xof'] / rate
        n = (fs['credit_xof'] + fs['debit_xof']) / rate
        country_review_html += f"""<tr>
            <td style="font-weight:600" data-sort="{flow}">{flow}</td>
            <td class="num" data-sort="{fs['count']}">{fs['count']:,}</td>
            <td class="num debit" data-sort="{d:.0f}">{d:,.0f}</td>
            <td class="num credit" data-sort="{c:.0f}">{c:,.0f}</td>
            <td class="num {'credit' if n >= 0 else 'debit'}" data-sort="{n:.0f}">{fmt_net(n)}</td>
        </tr>"""
    country_review_html += "</tbody></table></div></div>"

    # Category table
    country_review_html += """<div class="card"><div class="card-header">Transaction Types (USD)</div><div class="table-wrap"><div class="scroll-table"><table>
    <thead><tr><th class="sortable" data-col="0">Category</th><th class="sortable" data-col="1">Count</th>
    <th class="sortable" data-col="2">Outflows (USD)</th><th class="sortable" data-col="3">Inflows (USD)</th>
    <th class="sortable" data-col="4">Net (USD)</th></tr></thead><tbody>"""
    for cat, cs2 in sorted(cd['cat'].items(), key=lambda x: -x[1]['count']):
        d = cs2['debit_xof'] / rate
        c = cs2['credit_xof'] / rate
        n = (cs2['credit_xof'] + cs2['debit_xof']) / rate
        country_review_html += f"""<tr>
            <td data-sort="{cat}">{cat}</td>
            <td class="num" data-sort="{cs2['count']}">{cs2['count']:,}</td>
            <td class="num debit" data-sort="{d:.0f}">{d:,.0f}</td>
            <td class="num credit" data-sort="{c:.0f}">{c:,.0f}</td>
            <td class="num {'credit' if n >= 0 else 'debit'}" data-sort="{n:.0f}">{fmt_net(n)}</td>
        </tr>"""
    country_review_html += "</tbody></table></div></div></div>"

# Insights data computations
# Fee rate
total_fee_debit_xof = abs(cat_stats.get('Fees / Commissions', {}).get('debit_xof', 0)) + abs(cat_stats.get('Bank Charges', {}).get('debit_xof', 0))
total_payment_vol = abs(flow_stats.get('Payment', {}).get('debit_xof', 0))
fee_rate_pct = total_fee_debit_xof / total_payment_vol * 100 if total_payment_vol else 0
fee_rate_class = 'debit' if fee_rate_pct > 1.5 else 'credit'

# Cheque rate
cheque_count = cat_stats.get('Check / Cheque', {}).get('count', 0)
cheque_pct = cheque_count / data['total_count'] * 100

# SWIFT average
swift_stats = cat_stats.get('SWIFT / Telex', {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
swift_avg_usd = abs(swift_stats['debit_xof']) / swift_stats['count'] / rate if swift_stats['count'] else 0

# Banks below 1000 txns
low_activity_banks = [(bdn(b), s['count'], bank_to_country.get(b, 'Unknown')) for b, s in bank_stats.items() if s['count'] < 1000]
low_activity_banks.sort(key=lambda x: x[1])

# Other + Unclassified rate
other_count = cat_stats.get('Other', {}).get('count', 0)
unclass_count = cat_stats.get('Unclassified', {}).get('count', 0)
opacity_pct = (other_count + unclass_count) / data['total_count'] * 100

# Build consolidation candidates HTML
consolidation_html = ''
for bname, cnt, country in low_activity_banks:
    color = '#c53030' if cnt < 100 else '#b7791f' if cnt < 500 else '#718096'
    consolidation_html += f'<tr><td>{bname}</td><td>{country}</td><td class="num" style="color:{color};font-weight:600">{cnt:,}</td></tr>'

# Build insights HTML
insights_html = f"""
<div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:24px;">
    <div class="card" style="padding:20px;">
        <h3 style="color:var(--primary); margin-bottom:16px; font-size:16px;">Data Quality Metrics</h3>
        <table style="width:100%;font-size:13px;">
            <tr><td>Unclassified Rate</td><td class="num" style="font-weight:600;">{unclass_count/data['total_count']*100:.1f}%</td><td style="font-size:11px;color:var(--text-light)">Target: &lt;5%</td></tr>
            <tr><td>"Other" Rate</td><td class="num" style="font-weight:600;">{other_count/data['total_count']*100:.1f}%</td><td style="font-size:11px;color:var(--text-light)">Target: &lt;10%</td></tr>
            <tr><td>Combined Opacity</td><td class="num" style="font-weight:600;color:{'#c53030' if opacity_pct > 15 else '#276749'}">{opacity_pct:.1f}%</td><td style="font-size:11px;color:var(--text-light)">Target: &lt;15%</td></tr>
            <tr><td>Low-Activity Banks (&lt;1K txns)</td><td class="num" style="font-weight:600;">{len(low_activity_banks)}</td><td style="font-size:11px;color:var(--text-light)">Consolidation candidates</td></tr>
        </table>
    </div>
    <div class="card" style="padding:20px;">
        <h3 style="color:var(--primary); margin-bottom:16px; font-size:16px;">Operational Indicators</h3>
        <table style="width:100%;font-size:13px;">
            <tr><td>Fee/Commission Rate</td><td class="num" style="font-weight:600;color:{'#c53030' if fee_rate_pct > 1.5 else '#276749'}">{fee_rate_pct:.2f}%</td><td style="font-size:11px;color:var(--text-light)">of payment volume</td></tr>
            <tr><td>Cheque Volume</td><td class="num" style="font-weight:600;">{cheque_pct:.1f}%</td><td style="font-size:11px;color:var(--text-light)">{cheque_count:,} txns — target &lt;10%</td></tr>
            <tr><td>SWIFT/Telex Avg Value</td><td class="num" style="font-weight:600;">${swift_avg_usd:,.0f}</td><td style="font-size:11px;color:var(--text-light)">{swift_stats['count']} txns</td></tr>
            <tr><td>IAT Net Imbalance</td><td class="num" style="font-weight:600;color:#b7791f">${transfer_net:,.0f}</td><td style="font-size:11px;color:var(--text-light)">Should be ~$0</td></tr>
        </table>
    </div>
</div>

<div class="card" style="margin-bottom:20px;">
    <div class="card-header">Bank Consolidation Candidates (&lt;1,000 transactions over 26 months)</div>
    <div class="table-wrap"><table>
        <thead><tr><th>Bank</th><th>Country</th><th>Transaction Count</th></tr></thead>
        <tbody>{consolidation_html}</tbody>
    </table></div>
</div>
"""

# Country sections for insights
for country_name in sorted(country_stats.keys()):
    cd = country_detail[country_name]
    td_usd = cd['total_debit_xof'] / rate
    tc_usd = cd['total_credit_xof'] / rate
    tn_usd = (cd['total_credit_xof'] + cd['total_debit_xof']) / rate
    bank_count = len(cd['bank'])
    cheque_in_country = cd['cat'].get('Check / Cheque', {}).get('count', 0)
    other_in_country = cd['cat'].get('Other', {}).get('count', 0)
    unclass_in_country = cd['cat'].get('Unclassified', {}).get('count', 0)
    opacity_in_country = (other_in_country + unclass_in_country) / cd['total_count'] * 100 if cd['total_count'] else 0
    fee_in_country = cd['cat'].get('Fees / Commissions', {}).get('count', 0)

    # Top bank
    top_bank = max(cd['bank'].items(), key=lambda x: x[1]['count'])
    top_bank_pct = top_bank[1]['count'] / cd['total_count'] * 100

    insights_html += f"""
<div class="card" style="margin-bottom:20px;">
    <div class="card-header" style="background:var(--primary); color:#fff; font-size:16px;">{country_name} — Key Insights</div>
    <div style="padding:20px;">
        <div class="kpi-row" style="margin-bottom:16px;">
            <div class="kpi" style="padding:14px;">
                <div class="label">Transactions</div>
                <div class="value" style="font-size:20px;">{cd['total_count']:,}</div>
                <div class="sub">{bank_count} banks</div>
            </div>
            <div class="kpi" style="padding:14px;">
                <div class="label">Net Flow (USD)</div>
                <div class="value {'credit' if tn_usd >= 0 else 'debit'}" style="font-size:20px;">{'+' if tn_usd >= 0 else ''}${tn_usd/1e6:,.1f}M</div>
            </div>
            <div class="kpi" style="padding:14px;">
                <div class="label">Data Opacity</div>
                <div class="value" style="font-size:20px;color:{'#c53030' if opacity_in_country > 15 else '#b7791f' if opacity_in_country > 10 else '#276749'}">{opacity_in_country:.1f}%</div>
                <div class="sub">Other + Unclassified</div>
            </div>
            <div class="kpi" style="padding:14px;">
                <div class="label">Top Bank Concentration</div>
                <div class="value" style="font-size:20px;">{top_bank_pct:.0f}%</div>
                <div class="sub">{bdn(top_bank[0])}</div>
            </div>
        </div>
        <div style="font-size:13px; line-height:1.7; color:var(--text);">"""

    if country_name == 'Ivory Coast':
        insights_html += f"""
            <p><strong>Banking Fragmentation:</strong> {bank_count} banks is operationally heavy. Three banks have very low activity:
            Stanbic IC (7 txns), Citi IC (50 txns), Banque Populaire CI (325 txns). These generate compliance overhead
            (KYC renewals, signatory maintenance) with minimal operational value. Target: consolidate to 4-5 banks.</p>
            <p><strong>MTN Mobile Money ({cd['bank'].get('MTN Mobile FS CI', {}).get('count', 0):,} txns):</strong> Fourth-largest by volume. Mobile money is a genuine operational channel in Côte d'Ivoire.
            Confirm whether it's being used intentionally for a specific corridor (field supplier payments, last-mile collections) and integrate into TMS reporting.</p>
            <p><strong>Cheque Volume:</strong> {cheque_in_country:,} cheque transactions — needs investigation. In mature treasury ops, cheques should be &lt;2% of volume.
            Sample 200 cheque transactions, identify modernizable payees. Set 50% reduction target over 24 months.</p>
            <p><strong>Fee Transactions:</strong> {fee_in_country:,} fee line items suggests per-transaction pricing across multiple accounts. Request tariff schedules from all core banks and compare against actual charges.</p>"""
    elif country_name == 'Senegal':
        insights_html += f"""
            <p><strong>BICIS Concentration Risk:</strong> {bdn('BICIS Senegal')} handles {top_bank[1]['count']:,} txns ({top_bank_pct:.0f}% of country volume).
            Any BICIS outage has outsized impact. Need a formal bank contingency plan. Note: BNP Paribas has been rationalizing its Africa portfolio — monitor relationship risk annually.</p>
            <p><strong>CBAO + Bank Atlantique:</strong> Near-equal secondary banks ({cd['bank'].get('C.B.A.O. Senegal', {}).get('count', 0):,} and {cd['bank'].get('Bank Atlantique SN', {}).get('count', 0):,} txns).
            Confirm each has a distinct functional purpose (e.g., CBAO for collections, Atlantique for cross-border). If transactions are distributed without clear rationale, that's a routing governance gap.</p>
            <p><strong>Citi Senegal ({cd['bank'].get('Citi Senegal Bank', {}).get('count', 0):,} txns):</strong> Very high average value ($584K/txn — 60x portfolio average) with $11.9M net outflow.
            Requires account purpose documentation and counterparty review. If group Citi mandate exists, confirm West Africa is using it meaningfully.</p>
            <p><strong>Data Quality:</strong> Opacity rate of {opacity_in_country:.1f}% — likely driven by BICIS/CBAO BAI2 feed narrative configuration.
            Engage these banks specifically on populating transaction narrative fields consistently.</p>"""
    else:
        insights_html += f"<p>Review transaction patterns for anomalies.</p>"

    insights_html += """
        </div>
    </div>
</div>"""

# Priority actions
insights_html += """
<div class="card" style="margin-bottom:20px;">
    <div class="card-header" style="background:#975a16; color:#fff;">Priority Action Matrix</div>
    <div class="table-wrap"><table>
        <thead><tr><th>Priority</th><th>Action</th><th>Owner</th><th>Timeline</th></tr></thead>
        <tbody>
            <tr><td style="font-weight:600;color:#c53030;">1</td><td>Expand parser keyword rules — reduce "Other" by 40-60%</td><td>Data/IT</td><td>1 week</td></tr>
            <tr><td style="font-weight:600;color:#c53030;">2</td><td>Flag Unclassified &gt;$5K for manual review queue</td><td>Data/IT</td><td>1 week</td></tr>
            <tr><td style="font-weight:600;color:#b7791f;">3</td><td>Pull fee value total; compare to tariff schedules</td><td>Treasury</td><td>2 weeks</td></tr>
            <tr><td style="font-weight:600;color:#b7791f;">4</td><td>Sample 200 cheque txns — identify modernizable payees</td><td>Treasury Ops</td><td>3 weeks</td></tr>
            <tr><td style="font-weight:600;color:#b7791f;">5</td><td>Initiate Stanbic IC / Citi IC dormant account review</td><td>Treasury / Legal</td><td>4 weeks</td></tr>
            <tr><td style="font-weight:600;">6</td><td>Confirm intercompany cross-border transfer tax treatment</td><td>Tax / Legal</td><td>6 weeks</td></tr>
            <tr><td style="font-weight:600;">7</td><td>BICIS/CBAO BAI2 feed narrative configuration negotiation</td><td>Treasury / Banking</td><td>8 weeks</td></tr>
            <tr><td style="font-weight:600;">8</td><td>Bank rationalization plan (15 → 8 banks)</td><td>Treasury / Legal</td><td>12-18 months</td></tr>
        </tbody>
    </table></div>
</div>
"""

# Build bank-country mapping for cascading filter (Bonus)
bank_country_map = json.dumps(bank_to_country)
bank_display_map = json.dumps(BANK_DISPLAY)

# Date range for C-02
all_months = sorted(month_stats.keys())
min_month = all_months[0] if all_months else '2024-01'
max_month = all_months[-1] if all_months else '2025-12'

# Transaction JSON
txn_json = json.dumps(transactions)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PAGE_TITLE}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
    --primary: #1a365d;
    --primary-light: #2d5aa0;
    --accent: #c53030;
    --green: #1a6640;
    --bg: #f7fafc;
    --card: #fff;
    --border: #e2e8f0;
    --text: #2d3748;
    --text-light: #718096;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); }}
.header {{
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    color: #fff; padding: 28px 32px; margin-bottom: 24px;
}}
.header h1 {{ font-size: 24px; font-weight: 600; }}
.header .subtitle {{ color: #bee3f8; margin-top: 4px; font-size: 14px; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 0 24px 40px; }}

/* H-06: Exchange rate disclosure */
.rate-notice {{
    background: #fffbeb; border: 1px solid #f6e05e; border-radius: 6px;
    padding: 10px 16px; margin-bottom: 20px; font-size: 12px; color: #744210;
}}
.rate-notice strong {{ color: #975a16; }}

.kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.kpi {{ background: var(--card); border-radius: 8px; padding: 20px; border: 1px solid var(--border); }}
.kpi .label {{ font-size: 12px; text-transform: uppercase; color: var(--text-light); letter-spacing: 0.5px; margin-bottom: 4px; }}
.kpi .value {{ font-size: clamp(16px, 2.2vw, 24px); font-weight: 700; white-space: nowrap; }}
.kpi .sub {{ font-size: 12px; color: var(--text-light); margin-top: 2px; }}

/* C-03: Stronger color contrast + text indicators */
.debit {{ color: var(--accent); }}
.credit {{ color: var(--green); }}
.debit::before {{ content: '\\2193 '; }}
.credit::before {{ content: '\\2191 '; }}

.tabs {{ display: flex; gap: 0; border-bottom: 2px solid var(--border); margin-bottom: 20px; flex-wrap: wrap; }}
.tab {{ padding: 10px 20px; cursor: pointer; border: none; background: none; font-size: 14px; font-weight: 500; color: var(--text-light); border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.15s; }}
.tab:hover {{ color: var(--primary); background: #edf2f7; }}
.tab.active {{ color: var(--primary); border-bottom-color: var(--primary); }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.card {{ background: var(--card); border-radius: 8px; border: 1px solid var(--border); margin-bottom: 20px; overflow: hidden; }}
.card-header {{ padding: 16px 20px; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 15px; background: #f8fafc; }}

/* H-02: Responsive tables */
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; }}
th {{ background: var(--primary); color: #fff; padding: 10px 12px; text-align: left; font-weight: 500; position: sticky; top: 0; white-space: nowrap; }}
td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
tr:hover {{ background: #edf2f7; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}

/* C-01: Sortable headers */
th.sortable {{ cursor: pointer; user-select: none; position: relative; padding-right: 20px; }}
th.sortable::after {{ content: '\\2195'; position: absolute; right: 6px; opacity: 0.4; font-size: 11px; }}
th.sortable.asc::after {{ content: '\\2191'; opacity: 1; }}
th.sortable.desc::after {{ content: '\\2193'; opacity: 1; }}

/* H-04: Drill-through rows */
.drill-row {{ cursor: pointer; }}
.drill-row:hover {{ background: #ebf4ff !important; }}

.chart-container {{ padding: 20px; }}
.chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
@media (max-width: 900px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}
canvas {{ max-height: 350px; }}

/* C-04: Improved filter bar */
.filters {{ display: flex; gap: 10px; flex-wrap: wrap; padding: 14px 20px; background: #f8fafc; border-bottom: 1px solid var(--border); align-items: center; }}
.filters label {{ font-size: 11px; text-transform: uppercase; color: var(--text-light); letter-spacing: 0.3px; }}
.filter-group {{ display: flex; flex-direction: column; gap: 2px; }}
.filters select, .filters input {{ padding: 6px 10px; border: 1px solid var(--border); border-radius: 4px; font-size: 13px; }}
.filters input[type="text"] {{ width: 220px; }}
.filters input[type="month"] {{ width: 140px; }}
.btn {{ padding: 6px 14px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 500; transition: opacity 0.15s; }}
.btn:hover {{ opacity: 0.85; }}
.btn-primary {{ background: var(--primary); color: #fff; }}
.btn-success {{ background: var(--green); color: #fff; }}
.btn-outline {{ background: #fff; color: var(--text); border: 1px solid var(--border); }}

/* H-03: Pagination with page size */
.pagination {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: #f8fafc; border-top: 1px solid var(--border); font-size: 13px; gap: 12px; flex-wrap: wrap; }}
.pagination button {{ padding: 6px 14px; border: 1px solid var(--border); background: #fff; border-radius: 4px; cursor: pointer; }}
.pagination button:disabled {{ opacity: 0.4; cursor: default; }}
.pagination select {{ padding: 4px 8px; border: 1px solid var(--border); border-radius: 4px; font-size: 13px; }}
.scroll-table {{ max-height: 600px; overflow-y: auto; }}

/* Transaction table column widths */
#txnTable {{ table-layout: fixed; }}
#txnTable th:nth-child(1) {{ width: 90px; }}  /* Date */
#txnTable th:nth-child(2) {{ width: 95px; }}  /* Country */
#txnTable th:nth-child(3) {{ width: 160px; }} /* Bank */
#txnTable th:nth-child(4) {{ width: 100px; }} /* Ref */
#txnTable th:nth-child(5) {{ width: 110px; }} /* Category */
#txnTable th:nth-child(6) {{ width: auto; }}   /* Description */
#txnTable th:nth-child(7) {{ width: 120px; }} /* Beneficiary */
#txnTable th:nth-child(8) {{ width: 110px; }} /* XOF */
#txnTable th:nth-child(9) {{ width: 100px; }} /* USD */

/* Transfers table */
#tfTable {{ table-layout: fixed; }}

/* Cross-border highlight */
.cross-border-row {{ background: #eff6ff; }}

/* Insights grid responsive */
@media (max-width: 900px) {{
    #insights > div:first-child {{ grid-template-columns: 1fr !important; }}
}}

@media (max-width: 768px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .kpi .value {{ font-size: 18px; }}
    .filters {{ gap: 6px; }}
    .filter-group {{ flex: 1; min-width: 120px; }}
}}
</style>
</head>
<body>
<div class="header">
    <h1>{REPORT_TITLE}</h1>
    <div class="subtitle">{REPORT_SUBTITLE_REGION} | {data['total_count']:,} transactions | Generated {datetime.now().strftime('%B %d, %Y')}</div>
</div>
<div class="container">

<!-- H-06: Exchange rate disclosure -->
<div class="rate-notice">
    <strong>Exchange Rate Notice:</strong> All USD amounts are indicative, converted at a fixed rate of <strong>{rate:.0f} XOF per USD</strong> (approximate mid-market rate).
    Actual rates varied over the {min_month} to {max_month} period. XOF is pegged to EUR at 655.957 XOF/EUR. For precise USD values, apply date-specific exchange rates.
</div>

<div class="kpi-row">
    <div class="kpi">
        <div class="label">Total Transactions</div>
        <div class="value">{data['total_count']:,}</div>
        <div class="sub">15 banks across 2 countries</div>
    </div>
    <div class="kpi">
        <div class="label">Total Outflows (USD)</div>
        <div class="value debit">-${abs(total_debit_usd)/1e6:,.1f}M</div>
        <div class="sub">{abs(total_debit_xof)/1e9:,.1f}B XOF</div>
    </div>
    <div class="kpi">
        <div class="label">Total Inflows (USD)</div>
        <div class="value credit">+${total_credit_usd/1e6:,.1f}M</div>
        <div class="sub">{total_credit_xof/1e9:,.1f}B XOF</div>
    </div>
    <div class="kpi">
        <div class="label">Net Flow (USD)</div>
        <div class="value {'credit' if net_usd >= 0 else 'debit'}">{'+' if net_usd >= 0 else ''}${net_usd/1e6:,.1f}M</div>
        <div class="sub">{net_xof/1e6:,.0f}M XOF</div>
    </div>
    <div class="kpi">
        <div class="label">Unclassified Rate</div>
        <div class="value">{cat_stats.get('Unclassified', {}).get('count', 0) / data['total_count'] * 100:.1f}%</div>
        <div class="sub">{cat_stats.get('Unclassified', {}).get('count', 0):,} of {data['total_count']:,} transactions</div>
    </div>
    <div class="kpi">
        <div class="label">Date Range</div>
        <div class="value" style="font-size:18px">{min_month} to {max_month}</div>
        <div class="sub">{len(month_stats)} months of data</div>
    </div>
</div>

<div class="tabs" role="tablist">
    <button class="tab active" onclick="showTab('overview')" role="tab" aria-selected="true">Overview</button>
    <button class="tab" onclick="showTab('cashflow')" role="tab">Cash Flow</button>
    <button class="tab" onclick="showTab('country')" role="tab">Country</button>
    <button class="tab" onclick="showTab('categories')" role="tab">Transaction Types</button>
    <button class="tab" onclick="showTab('banks')" role="tab">Banks</button>
    <button class="tab" onclick="showTab('monthly')" role="tab">Monthly Trends</button>
    <button class="tab" onclick="showTab('countryreview')" role="tab">Country Review</button>
    <button class="tab" onclick="showTab('transfers')" role="tab">Transfers</button>
    <button class="tab" onclick="showTab('insights')" role="tab">Insights</button>
    <button class="tab" onclick="showTab('transactions')" role="tab">Transactions</button>
</div>

<!-- OVERVIEW TAB -->
<div id="overview" class="tab-content active" role="tabpanel">
    <div class="chart-row">
        <div class="card">
            <div class="card-header">Transaction Volume by Type</div>
            <div class="chart-container"><canvas id="catChart"></canvas></div>
        </div>
        <div class="card">
            <div class="card-header">Transaction Volume by Bank</div>
            <div class="chart-container"><canvas id="bankChart"></canvas></div>
        </div>
    </div>
    <div class="card">
        <div class="card-header">Monthly Cash Flow (USD) &mdash; Debits, Credits & Net Flow</div>
        <div class="chart-container"><canvas id="monthlyChart"></canvas></div>
    </div>
</div>

<!-- CASH FLOW TAB -->
<div id="cashflow" class="tab-content" role="tabpanel">
    <div class="kpi-row">
        <div class="kpi">
            <div class="label">Collections</div>
            <div class="value credit">+${collection_credits_usd:,.0f}</div>
            <div class="sub">{collection_count:,} transactions</div>
        </div>
        <div class="kpi">
            <div class="label">Payments</div>
            <div class="value debit">${payment_debits_usd:,.0f}</div>
            <div class="sub">{payment_count:,} transactions</div>
        </div>
        <div class="kpi">
            <div class="label">Operational Net</div>
            <div class="value {'credit' if ops_n >= 0 else 'debit'}">{'+' if ops_n >= 0 else ''}${ops_n:,.0f}</div>
            <div class="sub">Excl. inter-account transfers</div>
        </div>
        <div class="kpi">
            <div class="label">Inter-Account Transfers</div>
            <div class="value" style="font-size:18px">{transfer_count:,} txns</div>
            <div class="sub">Net: ${transfer_net:,.0f} (should be ~$0)</div>
        </div>
    </div>
    <div class="chart-row">
        <div class="card">
            <div class="card-header">Cash Flow by Type (USD)</div>
            <div class="chart-container"><canvas id="flowBarChart"></canvas></div>
        </div>
        <div class="card">
            <div class="card-header">Transaction Volume by Flow Type</div>
            <div class="chart-container"><canvas id="flowPieChart"></canvas></div>
        </div>
    </div>
    <div class="card">
        <div class="card-header">Flow Type Summary (USD) &mdash; click a row to view transactions</div>
        <div class="table-wrap"><div class="scroll-table">
        <table>
            <thead><tr>
                <th class="sortable" data-col="0">Flow Type</th>
                <th class="sortable" data-col="1">Count</th>
                <th class="sortable" data-col="2">Debits (USD)</th>
                <th class="sortable" data-col="3">Credits (USD)</th>
                <th class="sortable" data-col="4">Net (USD)</th>
            </tr></thead>
            <tbody>{flow_rows}</tbody>
            <tfoot>
                <tr style="font-weight:700; background:#edf2f7;">
                    <td>TOTAL</td>
                    <td class="num">{data['total_count']:,}</td>
                    <td class="num debit">{flow_total_d:,.0f}</td>
                    <td class="num credit">+{flow_total_c:,.0f}</td>
                    <td class="num {'credit' if flow_total_n >= 0 else 'debit'}">{fmt_net(flow_total_n)}</td>
                </tr>
                <tr style="font-weight:600; background:#ebf8ff; color: var(--primary);">
                    <td>OPERATIONAL (excl. transfers)</td>
                    <td class="num">{sum(s['count'] for s in ops_flows.values()):,}</td>
                    <td class="num debit">{ops_d:,.0f}</td>
                    <td class="num credit">+{ops_c:,.0f}</td>
                    <td class="num {'credit' if ops_n >= 0 else 'debit'}">{fmt_net(ops_n)}</td>
                </tr>
            </tfoot>
        </table>
        </div></div>
    </div>
</div>

<!-- COUNTRY TAB -->
<div id="country" class="tab-content" role="tabpanel">
    <div class="chart-row">
        <div class="card">
            <div class="card-header">Transaction Volume by Country</div>
            <div class="chart-container"><canvas id="countryPieChart"></canvas></div>
        </div>
        <div class="card">
            <div class="card-header">Cash Flow by Country (USD)</div>
            <div class="chart-container"><canvas id="countryBarChart"></canvas></div>
        </div>
    </div>
    <div class="card">
        <div class="card-header">Country Summary (USD) &mdash; click a row to view transactions</div>
        <div class="table-wrap"><div class="scroll-table">
        <table>
            <thead><tr>
                <th class="sortable" data-col="0">Country</th>
                <th class="sortable" data-col="1">Banks</th>
                <th class="sortable" data-col="2">Transactions</th>
                <th class="sortable" data-col="3">Debits (USD)</th>
                <th class="sortable" data-col="4">Credits (USD)</th>
                <th class="sortable" data-col="5">Net (USD)</th>
            </tr></thead>
            <tbody>{country_rows}</tbody>
        </table>
        </div></div>
    </div>
    <div class="card">
        <div class="card-header">Banks by Country (USD) &mdash; click a row to view transactions</div>
        <div class="table-wrap"><div class="scroll-table">
        <table>
            <thead><tr>
                <th class="sortable" data-col="0">Country</th>
                <th class="sortable" data-col="1">Bank</th>
                <th class="sortable" data-col="2">Transactions</th>
                <th class="sortable" data-col="3">Debits (USD)</th>
                <th class="sortable" data-col="4">Credits (USD)</th>
                <th class="sortable" data-col="5">Net (USD)</th>
            </tr></thead>
            <tbody>{country_bank_rows}</tbody>
        </table>
        </div></div>
    </div>
</div>

<!-- CATEGORIES TAB -->
<div id="categories" class="tab-content" role="tabpanel">
    <div class="card">
        <div class="card-header">Transaction Types (Parsed from Comment Field) &mdash; click a row to view transactions</div>
        <div class="table-wrap"><div class="scroll-table">
        <table>
            <thead><tr>
                <th class="sortable" data-col="0">Category</th>
                <th class="sortable" data-col="1">Count</th>
                <th class="sortable" data-col="2">Debits (USD)</th>
                <th class="sortable" data-col="3">Credits (USD)</th>
                <th class="sortable" data-col="4">Net (USD)</th>
            </tr></thead>
            <tbody>{cat_rows}</tbody>
            <tfoot><tr style="font-weight:700; background:#edf2f7;">
                <td>TOTAL</td>
                <td class="num">{data['total_count']:,}</td>
                <td class="num debit">{total_debit_usd:,.0f}</td>
                <td class="num credit">+{total_credit_usd:,.0f}</td>
                <td class="num {'credit' if net_usd >= 0 else 'debit'}">{fmt_net(net_usd)}</td>
            </tr></tfoot>
        </table>
        </div></div>
    </div>
</div>

<!-- BANKS TAB -->
<div id="banks" class="tab-content" role="tabpanel">
    <div class="card">
        <div class="card-header">Bank Summary (USD) &mdash; click a row to view transactions</div>
        <div class="table-wrap"><div class="scroll-table">
        <table>
            <thead><tr>
                <th class="sortable" data-col="0">Bank</th>
                <th class="sortable" data-col="1">Country</th>
                <th class="sortable" data-col="2">Count</th>
                <th class="sortable" data-col="3">Debits (USD)</th>
                <th class="sortable" data-col="4">Credits (USD)</th>
                <th class="sortable" data-col="5">Net (USD)</th>
            </tr></thead>
            <tbody>{bank_rows}</tbody>
        </table>
        </div></div>
    </div>
</div>

<!-- MONTHLY TAB -->
<div id="monthly" class="tab-content" role="tabpanel">
    <div class="card">
        <div class="card-header">Monthly Breakdown (USD)</div>
        <div class="table-wrap"><div class="scroll-table">
        <table>
            <thead><tr>
                <th class="sortable" data-col="0">Month</th>
                <th class="sortable" data-col="1">Count</th>
                <th class="sortable" data-col="2">Debits (USD)</th>
                <th class="sortable" data-col="3">Credits (USD)</th>
                <th class="sortable" data-col="4">Net (USD)</th>
            </tr></thead>
            <tbody>{month_rows}</tbody>
        </table>
        </div></div>
    </div>
</div>

<!-- COUNTRY REVIEW TAB -->
<div id="countryreview" class="tab-content" role="tabpanel">
    <div class="card" style="padding:16px 20px; margin-bottom:20px;">
        <p style="font-size:13px; color:var(--text-light);">Detailed per-country breakdown of transactions, banks, flow types, and categories. Click any bank row to drill through to transactions.</p>
    </div>
    {country_review_html}
</div>

<!-- TRANSFERS TAB -->
<div id="transfers" class="tab-content" role="tabpanel">
    <div class="kpi-row">
        <div class="kpi">
            <div class="label">Total Matched Pairs</div>
            <div class="value">{len(transfers):,}</div>
            <div class="sub">Same-date, same-amount, different accounts</div>
        </div>
        <div class="kpi">
            <div class="label">Intra-Entity</div>
            <div class="value">{intra_country_count:,}</div>
            <div class="sub">${intra_total_usd:,.0f} USD | Post float: {intra_avg_float:.1f}d | Value float: {intra_avg_vfloat:.1f}d</div>
        </div>
        <div class="kpi">
            <div class="label">Intercompany</div>
            <div class="value">{cross_border_count:,}</div>
            <div class="sub">${ic_total_usd:,.0f} USD | Post float: {ic_avg_float:.1f}d | Value float: {ic_avg_vfloat:.1f}d</div>
        </div>
        <div class="kpi">
            <div class="label">Avg Float (Posted)</div>
            <div class="value" style="color:{'#276749' if avg_float < 1 else '#b7791f' if avg_float < 3 else '#c53030'}">{avg_float:.1f}d</div>
            <div class="sub">Same-day: {zero_float:,} | Max: {max_float}d</div>
        </div>
        <div class="kpi">
            <div class="label">Avg Float (Value Date)</div>
            <div class="value" style="color:{'#276749' if avg_vfloat < 1 else '#b7791f' if avg_vfloat < 3 else '#c53030'}">{avg_vfloat:.1f}d</div>
            <div class="sub">Based on bank value dates</div>
        </div>
    </div>

    <!-- INTRA-ENTITY TRANSFERS TABLE -->
    <div class="card">
        <div class="card-header">Intra-Entity Transfers &mdash; Account to Account<span style="font-size:12px;font-weight:400;color:var(--text-light);margin-left:12px;">{intra_country_count:,} pairs | Post float: {intra_avg_float:.1f}d | Value float: {intra_avg_vfloat:.1f}d</span></div>
        <div class="filters" style="padding:12px 16px;border-bottom:1px solid var(--border);">
            <div class="filter-group"><label>From</label><input type="month" id="intraFrom" value="{min_month}" min="{min_month}" max="{max_month}" onchange="renderIntra()"></div>
            <div class="filter-group"><label>To</label><input type="month" id="intraTo" value="{max_month}" min="{min_month}" max="{max_month}" onchange="renderIntra()"></div>
            <div class="filter-group"><label>Search</label><input type="text" id="intraSearch" placeholder="Bank, description..." oninput="clearTimeout(intraTimer);intraTimer=setTimeout(renderIntra,300)"></div>
            <div class="filter-group" style="justify-content:flex-end;"><label>&nbsp;</label>
                <div style="display:flex;gap:6px;">
                    <button class="btn btn-outline" onclick="document.getElementById('intraFrom').value='{min_month}';document.getElementById('intraTo').value='{max_month}';document.getElementById('intraSearch').value='';renderIntra()">Clear</button>
                    <button class="btn btn-success" onclick="exportIntraCSV()">Export CSV</button>
                </div>
            </div>
        </div>
        <div class="table-wrap"><div class="scroll-table" style="max-height:600px;">
            <table>
                <thead><tr>
                    <th>From Bank</th>
                    <th style="width:45px">Acct</th>
                    <th>To Bank</th>
                    <th style="width:45px">Acct</th>
                    <th>Amount (USD)</th>
                    <th>Amount (XOF)</th>
                    <th style="white-space:nowrap;font-size:11px">Posted Out</th>
                    <th style="white-space:nowrap;font-size:11px">Posted In</th>
                    <th style="font-size:11px" title="Float based on PostedDate">PF</th>
                    <th style="white-space:nowrap;font-size:11px">Value Out</th>
                    <th style="white-space:nowrap;font-size:11px">Value In</th>
                    <th style="font-size:11px" title="Float based on ValueDate">VF</th>
                    <th style="min-width:200px">Description</th>
                </tr></thead>
                <tbody id="intraBody"></tbody>
            </table>
        </div></div>
        <div class="pagination">
            <span id="intraPageInfo"></span>
            <div style="display:flex;align-items:center;gap:10px;">
                <button id="intraPrev" onclick="intraPage--;renderIntra()">Previous</button>
                <button id="intraNext" onclick="intraPage++;renderIntra()">Next</button>
            </div>
        </div>
    </div>

    <!-- INTERCOMPANY TRANSFERS TABLE -->
    <div class="card">
        <div class="card-header" style="background:#ebf8ff;">Intercompany Transfers &mdash; Cross-Entity<span style="font-size:12px;font-weight:400;color:var(--text-light);margin-left:12px;">{cross_border_count:,} pairs | Post float: {ic_avg_float:.1f}d | Value float: {ic_avg_vfloat:.1f}d</span></div>
        <div class="filters" style="padding:12px 16px;border-bottom:1px solid var(--border);">
            <div class="filter-group"><label>From</label><input type="month" id="icFrom" value="{min_month}" min="{min_month}" max="{max_month}" onchange="renderIC()"></div>
            <div class="filter-group"><label>To</label><input type="month" id="icTo" value="{max_month}" min="{min_month}" max="{max_month}" onchange="renderIC()"></div>
            <div class="filter-group"><label>Search</label><input type="text" id="icSearch" placeholder="Bank, description..." oninput="clearTimeout(icTimer);icTimer=setTimeout(renderIC,300)"></div>
            <div class="filter-group" style="justify-content:flex-end;"><label>&nbsp;</label>
                <div style="display:flex;gap:6px;">
                    <button class="btn btn-outline" onclick="document.getElementById('icFrom').value='{min_month}';document.getElementById('icTo').value='{max_month}';document.getElementById('icSearch').value='';renderIC()">Clear</button>
                    <button class="btn btn-success" onclick="exportICCSV()">Export CSV</button>
                </div>
            </div>
        </div>
        <div class="table-wrap"><div class="scroll-table" style="max-height:600px;">
            <table>
                <thead><tr>
                    <th>From Bank</th>
                    <th style="width:45px">Acct</th>
                    <th>From Entity</th>
                    <th>To Bank</th>
                    <th style="width:45px">Acct</th>
                    <th>To Entity</th>
                    <th>Amount (USD)</th>
                    <th>Amount (XOF)</th>
                    <th style="white-space:nowrap;font-size:11px">Posted Out</th>
                    <th style="white-space:nowrap;font-size:11px">Posted In</th>
                    <th style="font-size:11px" title="Float based on PostedDate">PF</th>
                    <th style="white-space:nowrap;font-size:11px">Value Out</th>
                    <th style="white-space:nowrap;font-size:11px">Value In</th>
                    <th style="font-size:11px" title="Float based on ValueDate">VF</th>
                    <th style="min-width:200px">Description</th>
                </tr></thead>
                <tbody id="icBody"></tbody>
            </table>
        </div></div>
        <div class="pagination">
            <span id="icPageInfo"></span>
            <div style="display:flex;align-items:center;gap:10px;">
                <button id="icPrev" onclick="icPage--;renderIC()">Previous</button>
                <button id="icNext" onclick="icPage++;renderIC()">Next</button>
            </div>
        </div>
    </div>
</div>

<!-- INSIGHTS TAB -->
<div id="insights" class="tab-content" role="tabpanel">
    {insights_html}
</div>

<!-- TRANSACTIONS TAB -->
<div id="transactions" class="tab-content" role="tabpanel">
    <div class="card">
        <div class="filters">
            <div class="filter-group">
                <label>Country</label>
                <select id="filterCountry" onchange="onCountryChange()"><option value="">All Countries</option></select>
            </div>
            <div class="filter-group">
                <label>Bank</label>
                <select id="filterBank" onchange="applyFilters()"><option value="">All Banks</option></select>
            </div>
            <div class="filter-group">
                <label>Flow</label>
                <select id="filterFlow" onchange="applyFilters()"><option value="">All Flows</option></select>
            </div>
            <div class="filter-group">
                <label>Type</label>
                <select id="filterCat" onchange="applyFilters()"><option value="">All Types</option></select>
            </div>
            <div class="filter-group">
                <label>Direction</label>
                <select id="filterDir" onchange="applyFilters()"><option value="">All</option><option value="debit">Debits</option><option value="credit">Credits</option></select>
            </div>
            <div class="filter-group">
                <label>From</label>
                <input type="month" id="filterFrom" value="{min_month}" min="{min_month}" max="{max_month}" onchange="applyFilters()">
            </div>
            <div class="filter-group">
                <label>To</label>
                <input type="month" id="filterTo" value="{max_month}" min="{min_month}" max="{max_month}" onchange="applyFilters()">
            </div>
            <div class="filter-group">
                <label>Search</label>
                <input type="text" id="filterSearch" placeholder="Description, ref, beneficiary...">
            </div>
            <div class="filter-group" style="justify-content:flex-end;">
                <label>&nbsp;</label>
                <div style="display:flex;gap:6px;">
                    <button class="btn btn-outline" onclick="clearFilters()">Clear</button>
                    <button class="btn btn-success" onclick="exportCSV()">Export CSV</button>
                </div>
            </div>
        </div>
        <div class="table-wrap"><div class="scroll-table" style="max-height:700px;">
            <table id="txnTable">
                <thead><tr>
                    <th>Date</th><th>Country</th><th>Bank</th><th>Ref</th><th>Category</th>
                    <th>Description</th><th>Beneficiary</th>
                    <th>Amount (XOF)</th><th>Amount (USD)</th>
                </tr></thead>
                <tbody id="txnBody"></tbody>
            </table>
        </div></div>
        <div class="pagination">
            <span id="pageInfo"></span>
            <div style="display:flex;align-items:center;gap:10px;">
                <label style="font-size:12px;color:var(--text-light);">Rows:</label>
                <select id="pageSizeSel" onchange="changePageSize()">
                    <option value="100">100</option>
                    <option value="200" selected>200</option>
                    <option value="500">500</option>
                    <option value="1000">1000</option>
                </select>
                <button id="prevBtn" onclick="changePage(-1)">Previous</button>
                <button id="nextBtn" onclick="changePage(1)">Next</button>
            </div>
        </div>
    </div>
</div>

</div>

<script>
const ALL_TXN = {txn_json};
const BANK_COUNTRY = {bank_country_map};
const BANK_DISPLAY = {bank_display_map};
let filtered = ALL_TXN;
let page = 0;
let pageSize = 200;

// Populate filter dropdowns
const allCountries = [...new Set(ALL_TXN.map(t => t.country))].sort();
const allBanks = [...new Set(ALL_TXN.map(t => t.bank))].sort();
const allCats = [...new Set(ALL_TXN.map(t => t.category))].sort();
const allFlows = [...new Set(ALL_TXN.map(t => t.flow_type))].sort();
const countrySel = document.getElementById('filterCountry');
const bankSel = document.getElementById('filterBank');
const catSel = document.getElementById('filterCat');
const flowSel = document.getElementById('filterFlow');
allCountries.forEach(c => {{ const o = document.createElement('option'); o.value = c; o.textContent = c; countrySel.appendChild(o); }});
allBanks.forEach(b => {{ const o = document.createElement('option'); o.value = b; o.textContent = BANK_DISPLAY[b] || b; bankSel.appendChild(o); }});
allCats.forEach(c => {{ const o = document.createElement('option'); o.value = c; o.textContent = c; catSel.appendChild(o); }});
allFlows.forEach(f => {{ const o = document.createElement('option'); o.value = f; o.textContent = f; flowSel.appendChild(o); }});

// Bonus: Cascading country -> bank filter
function onCountryChange() {{
    const selCountry = countrySel.value;
    const currentBank = bankSel.value;
    bankSel.innerHTML = '<option value="">All Banks</option>';
    const banksToShow = selCountry
        ? allBanks.filter(b => BANK_COUNTRY[b] === selCountry)
        : allBanks;
    banksToShow.forEach(b => {{
        const o = document.createElement('option');
        o.value = b; o.textContent = BANK_DISPLAY[b] || b;
        if (b === currentBank) o.selected = true;
        bankSel.appendChild(o);
    }});
    applyFilters();
}}

// C-04: Debounced search
let searchTimer = null;
document.getElementById('filterSearch').addEventListener('input', () => {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilters, 300);
}});

function applyFilters() {{
    const country = countrySel.value;
    const bank = bankSel.value;
    const cat = catSel.value;
    const flow = flowSel.value;
    const dir = document.getElementById('filterDir').value;
    const from = document.getElementById('filterFrom').value;
    const to = document.getElementById('filterTo').value;
    const search = document.getElementById('filterSearch').value.toLowerCase();
    filtered = ALL_TXN.filter(t => {{
        if (country && t.country !== country) return false;
        if (bank && t.bank !== bank) return false;
        if (cat && t.category !== cat) return false;
        if (flow && t.flow_type !== flow) return false;
        if (dir === 'debit' && t.amount_xof >= 0) return false;
        if (dir === 'credit' && t.amount_xof < 0) return false;
        if (from && t.month < from) return false;
        if (to && t.month > to) return false;
        if (search && !(t.description||'').toLowerCase().includes(search) && !(t.ref||'').toLowerCase().includes(search) && !(t.beneficiary||'').toLowerCase().includes(search) && !(t.bank||'').toLowerCase().includes(search)) return false;
        return true;
    }});
    page = 0;
    renderTxns();
}}

// C-04: Clear filters
function clearFilters() {{
    countrySel.value = '';
    onCountryChange();
    catSel.value = '';
    flowSel.value = '';
    document.getElementById('filterDir').value = '';
    document.getElementById('filterFrom').value = '{min_month}';
    document.getElementById('filterTo').value = '{max_month}';
    document.getElementById('filterSearch').value = '';
    filtered = ALL_TXN;
    page = 0;
    renderTxns();
}}

function renderTxns() {{
    const start = page * pageSize;
    const end = Math.min(start + pageSize, filtered.length);
    const tbody = document.getElementById('txnBody');
    let html = '';
    for (let i = start; i < end; i++) {{
        const t = filtered[i];
        const cls = t.amount_xof < 0 ? 'debit' : 'credit';
        const prefix = t.amount_xof < 0 ? '' : '+';
        const prefixU = t.amount_usd < 0 ? '-$' : '+$';
        html += '<tr><td>' + t.date + '</td><td>' + t.country + '</td><td>' + (BANK_DISPLAY[t.bank]||t.bank) + '</td><td>' + t.ref + '</td><td>' + t.category + '</td><td title="' + (t.description||'').replace(/"/g,'&quot;') + '">' + (t.description||'') + '</td><td title="' + (t.beneficiary||'').replace(/"/g,'&quot;') + '">' + (t.beneficiary||'') + '</td><td class="num ' + cls + '">' + prefix + t.amount_xof.toLocaleString('en-US') + '</td><td class="num ' + cls + '">' + prefixU + Math.abs(t.amount_usd).toLocaleString('en-US') + '</td></tr>';
    }}
    if (filtered.length === 0) {{
        html = '<tr><td colspan="9" style="text-align:center; padding:48px 20px; color:#64748b;">'
            + '<div style="font-size:32px; margin-bottom:12px;">&#x1F50D;</div>'
            + '<div style="font-weight:600; font-size:15px; margin-bottom:6px;">No transactions match your filters</div>'
            + '<div style="font-size:13px;">Try widening the date range, clearing the search term, or removing a filter.</div>'
            + '<button onclick="clearFilters()" style="margin-top:16px; padding:8px 20px; border:1px solid #cbd5e1; border-radius:6px; cursor:pointer; font-size:13px;">Clear All Filters</button>'
            + '</td></tr>';
    }}
    tbody.innerHTML = html;
    const showing = filtered.length === 0 ? 'No transactions match filters' : 'Showing ' + (start+1).toLocaleString('en-US') + '-' + end.toLocaleString('en-US') + ' of ' + filtered.length.toLocaleString('en-US');
    document.getElementById('pageInfo').textContent = showing;
    document.getElementById('prevBtn').disabled = page === 0;
    document.getElementById('nextBtn').disabled = end >= filtered.length;
}}

function changePage(d) {{ page += d; renderTxns(); }}

// H-03: Page size control
function changePageSize() {{
    pageSize = parseInt(document.getElementById('pageSizeSel').value);
    page = 0;
    renderTxns();
}}

function exportCSV() {{
    let csv = 'Date,Country,Bank,Account,Ref,Category,Description,Beneficiary,Amount_XOF,Amount_USD\\n';
    filtered.forEach(t => {{
        csv += [t.date, '"'+t.country+'"', '"'+(BANK_DISPLAY[t.bank]||t.bank)+'"', '"'+t.account+'"', t.ref, '"'+t.category+'"', '"'+(t.description||'').replace(/"/g,"''")+'"', '"'+(t.beneficiary||'').replace(/"/g,"''")+'"', t.amount_xof, t.amount_usd].join(',') + '\\n';
    }});
    const blob = new Blob([csv], {{type:'text/csv'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '{CSV_FILENAME}';
    a.click();
}}

function showTab(id) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(el => {{
        el.classList.remove('active');
        el.setAttribute('aria-selected', 'false');
    }});
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
    event.target.setAttribute('aria-selected', 'true');
    if (id === 'transactions') renderTxns();
    if (id === 'transfers') renderTransfers();
}}

// H-04: Drill-through — click summary row to jump to filtered transactions
document.addEventListener('click', function(e) {{
    const row = e.target.closest('.drill-row');
    if (!row) return;
    const type = row.dataset.filterType;
    const value = row.dataset.filterValue;
    // Reset all filters first
    countrySel.value = '';
    onCountryChange();
    catSel.value = '';
    flowSel.value = '';
    document.getElementById('filterDir').value = '';
    document.getElementById('filterFrom').value = '{min_month}';
    document.getElementById('filterTo').value = '{max_month}';
    document.getElementById('filterSearch').value = '';
    // Set the relevant filter
    if (type === 'country') {{
        countrySel.value = value;
        onCountryChange();
    }} else if (type === 'bank') {{
        const bCountry = BANK_COUNTRY[value] || '';
        if (bCountry) {{ countrySel.value = bCountry; onCountryChange(); }}
        bankSel.value = value;
    }} else if (type === 'category') {{
        catSel.value = value;
    }} else if (type === 'flow') {{
        flowSel.value = value;
    }}
    applyFilters();
    showTabById('transactions');
}});

function showTabById(id) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(el => {{
        el.classList.remove('active');
        el.setAttribute('aria-selected', 'false');
        if (el.textContent.trim().toLowerCase() === id || el.onclick.toString().includes("'" + id + "'")) {{
            el.classList.add('active');
            el.setAttribute('aria-selected', 'true');
        }}
    }});
    document.getElementById(id).classList.add('active');
    if (id === 'transactions') renderTxns();
    if (id === 'transfers') renderTransfers();
}}

// C-01: Table sorting
document.querySelectorAll('th.sortable').forEach(th => {{
    th.addEventListener('click', function() {{
        const table = this.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const col = parseInt(this.dataset.col);
        const isAsc = this.classList.contains('asc');

        // Clear other sort indicators in this table
        table.querySelectorAll('th.sortable').forEach(h => h.classList.remove('asc','desc'));

        rows.sort((a, b) => {{
            const aVal = a.cells[col].dataset.sort || a.cells[col].textContent;
            const bVal = b.cells[col].dataset.sort || b.cells[col].textContent;
            const aNum = parseFloat(aVal.replace(/,/g, ''));
            const bNum = parseFloat(bVal.replace(/,/g, ''));
            if (!isNaN(aNum) && !isNaN(bNum)) {{
                return isAsc ? bNum - aNum : aNum - bNum;
            }}
            return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        }});

        this.classList.add(isAsc ? 'desc' : 'asc');
        rows.forEach(r => tbody.appendChild(r));
    }});
}});

// Charts
const catColors = ['#3182ce','#c53030','#276749','#b7791f','#6b46c1','#c05621','#2c7a7b','#9b2c2c','#5a67d8','#b83280','#319795','#dd6b20','#e53e3e','#38a169'];

new Chart(document.getElementById('catChart'), {{
    type: 'bar',
    data: {{
        labels: {cat_labels},
        datasets: [{{ label: 'Transactions', data: {cat_counts}, backgroundColor: catColors }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ ticks: {{ maxRotation: 45, font: {{ size: 10 }} }} }}, y: {{ ticks: {{ callback: v => v.toLocaleString() }} }} }}
    }}
}});

// H06: Top-6 banks + Other aggregation
(function() {{
    const bkLabelsRaw = {bk_labels};
    const bkCountsRaw = {bk_counts};
    const bkPairs = bkLabelsRaw.map((l,i) => [l, bkCountsRaw[i]]).sort((a,b) => b[1] - a[1]);
    const TOP_N = 6;
    const topLabels = bkPairs.slice(0, TOP_N).map(p => p[0]);
    const topCounts = bkPairs.slice(0, TOP_N).map(p => p[1]);
    const otherCount = bkPairs.slice(TOP_N).reduce((s,p) => s + p[1], 0);
    topLabels.push('Other Banks (' + (bkPairs.length - TOP_N) + ')');
    topCounts.push(otherCount);
    new Chart(document.getElementById('bankChart'), {{
        type: 'bar',
        data: {{
            labels: topLabels,
            datasets: [{{ label: 'Transactions', data: topCounts, backgroundColor: catColors }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{ x: {{ ticks: {{ callback: v => v.toLocaleString('en-US') }} }} }}
        }}
    }});
}})();

// H-01: Monthly chart with absolute debits + net flow line
new Chart(document.getElementById('monthlyChart'), {{
    type: 'bar',
    data: {{
        labels: {month_labels},
        datasets: [
            {{ label: 'Debits (USD)', data: {month_debits_abs}, backgroundColor: 'rgba(197,48,48,0.7)', order: 2 }},
            {{ label: 'Credits (USD)', data: {month_credits}, backgroundColor: 'rgba(39,103,73,0.7)', order: 2 }},
            {{ label: 'Net Flow (USD)', data: {month_net}, type: 'line', borderColor: '#5a67d8', backgroundColor: 'rgba(90,103,216,0.1)', borderWidth: 2, pointRadius: 3, fill: false, order: 1 }}
        ]
    }},
    options: {{
        responsive: true,
        interaction: {{ mode: 'index', intersect: false }},
        scales: {{ y: {{ ticks: {{ callback: v => '$' + (v/1e6).toFixed(1) + 'M' }} }} }},
        plugins: {{ tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': $' + Math.abs(ctx.raw).toLocaleString() }} }} }}
    }}
}});

// Country charts
new Chart(document.getElementById('countryPieChart'), {{
    type: 'pie',
    data: {{
        labels: {country_labels},
        datasets: [{{ data: {country_counts}, backgroundColor: ['#3182ce','#c53030','#276749','#b7791f'] }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ position: 'bottom' }},
            tooltip: {{ callbacks: {{ label: ctx => ctx.label + ': ' + ctx.raw.toLocaleString() + ' txns (' + (ctx.raw / {data['total_count']} * 100).toFixed(1) + '%)' }} }}
        }}
    }}
}});

new Chart(document.getElementById('countryBarChart'), {{
    type: 'bar',
    data: {{
        labels: {country_labels},
        datasets: [
            {{ label: 'Debits (USD)', data: {country_debits_usd}, backgroundColor: 'rgba(197,48,48,0.7)' }},
            {{ label: 'Credits (USD)', data: {country_credits_usd}, backgroundColor: 'rgba(39,103,73,0.7)' }}
        ]
    }},
    options: {{
        responsive: true,
        scales: {{ y: {{ ticks: {{ callback: v => '$' + (v/1e6).toFixed(1) + 'M' }} }} }},
        plugins: {{ tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': $' + Math.abs(ctx.raw).toLocaleString() }} }} }}
    }}
}});

// Flow charts
const flowColors = ['#276749','#c53030','#5a67d8','#b7791f','#6b46c1','#2c7a7b','#718096'];

new Chart(document.getElementById('flowBarChart'), {{
    type: 'bar',
    data: {{
        labels: {flow_labels},
        datasets: [
            {{ label: 'Debits (USD)', data: {flow_debits_usd}, backgroundColor: 'rgba(197,48,48,0.7)' }},
            {{ label: 'Credits (USD)', data: {flow_credits_usd}, backgroundColor: 'rgba(39,103,73,0.7)' }}
        ]
    }},
    options: {{
        responsive: true,
        scales: {{ y: {{ ticks: {{ callback: v => '$' + (v/1e6).toFixed(1) + 'M' }} }} }},
        plugins: {{ tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': $' + Math.abs(ctx.raw).toLocaleString() }} }} }}
    }}
}});

new Chart(document.getElementById('flowPieChart'), {{
    type: 'doughnut',
    data: {{
        labels: {flow_labels},
        datasets: [{{ data: {flow_counts}, backgroundColor: flowColors }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ position: 'bottom' }},
            tooltip: {{ callbacks: {{ label: ctx => ctx.label + ': ' + ctx.raw.toLocaleString() + ' txns' }} }}
        }}
    }}
}});

// --- TRANSFERS TAB ---
const INTRA_TF = {intra_transfers_json};
const IC_TF = {ic_transfers_json};
let intraPage = 0, icPage = 0;
let intraTimer = null, icTimer = null;
const tfPageSize = 200;

function floatBadge(days) {{
    if (days === null) return '-';
    const color = days === 0 ? '#276749' : days <= 2 ? '#b7791f' : '#c53030';
    return '<span style="font-weight:600;color:' + color + '">' + days + 'd</span>';
}}

function filterTF(list, fromId, toId, searchId) {{
    const from = document.getElementById(fromId).value;
    const to = document.getElementById(toId).value;
    const search = document.getElementById(searchId).value.toLowerCase();
    return list.filter(t => {{
        const month = (t.debit_date||t.date).substring(0, 7);
        if (from && month < from) return false;
        if (to && month > to) return false;
        if (search && !(t.description||'').toLowerCase().includes(search)
            && !(t.source_bank||'').toLowerCase().includes(search)
            && !(t.dest_bank||'').toLowerCase().includes(search)
            && !(t.debit_desc||'').toLowerCase().includes(search)
            && !(t.credit_desc||'').toLowerCase().includes(search)) return false;
        return true;
    }});
}}

function renderIntra() {{
    const filtered = filterTF(INTRA_TF, 'intraFrom', 'intraTo', 'intraSearch');
    const start = intraPage * tfPageSize;
    const end = Math.min(start + tfPageSize, filtered.length);
    let html = '';
    for (let i = start; i < end; i++) {{
        const t = filtered[i];
        const srcAcct = t.source_account ? t.source_account.slice(-4) : '';
        const dstAcct = t.dest_account ? t.dest_account.slice(-4) : '';
        const desc = t.debit_desc || t.credit_desc || t.description || '-';
        html += '<tr>'
            + '<td>' + (BANK_DISPLAY[t.source_bank]||t.source_bank) + '</td>'
            + '<td style="font-family:monospace;font-size:11px;color:#4a5568;text-align:center">' + srcAcct + '</td>'
            + '<td>' + (BANK_DISPLAY[t.dest_bank]||t.dest_bank) + '</td>'
            + '<td style="font-family:monospace;font-size:11px;color:#4a5568;text-align:center">' + dstAcct + '</td>'
            + '<td class="num">$' + t.amount_usd.toLocaleString('en-US', {{minimumFractionDigits:0}}) + '</td>'
            + '<td class="num">' + t.amount_xof.toLocaleString('en-US', {{maximumFractionDigits:0}}) + '</td>'
            + '<td style="white-space:nowrap;font-size:11px">' + (t.debit_date||'-') + '</td>'
            + '<td style="white-space:nowrap;font-size:11px">' + (t.credit_date||'-') + '</td>'
            + '<td class="num" style="font-size:11px">' + floatBadge(t.float_days) + '</td>'
            + '<td style="white-space:nowrap;font-size:11px;color:#6b46c1">' + (t.debit_value_date||'-') + '</td>'
            + '<td style="white-space:nowrap;font-size:11px;color:#6b46c1">' + (t.credit_value_date||'-') + '</td>'
            + '<td class="num" style="font-size:11px">' + floatBadge(t.value_float_days) + '</td>'
            + '<td title="' + desc.replace(/"/g,'&quot;') + '">' + desc + '</td>'
            + '</tr>';
    }}
    if (filtered.length === 0) html = '<tr><td colspan="13" style="text-align:center;padding:40px;color:#64748b;">No intra-entity transfers match filters</td></tr>';
    document.getElementById('intraBody').innerHTML = html;
    document.getElementById('intraPageInfo').textContent = filtered.length === 0 ? 'No matches' : 'Showing ' + (start+1) + '-' + end + ' of ' + filtered.length;
    document.getElementById('intraPrev').disabled = intraPage === 0;
    document.getElementById('intraNext').disabled = end >= filtered.length;
}}

function renderIC() {{
    const filtered = filterTF(IC_TF, 'icFrom', 'icTo', 'icSearch');
    const start = icPage * tfPageSize;
    const end = Math.min(start + tfPageSize, filtered.length);
    let html = '';
    for (let i = start; i < end; i++) {{
        const t = filtered[i];
        const srcAcct = t.source_account ? t.source_account.slice(-4) : '';
        const dstAcct = t.dest_account ? t.dest_account.slice(-4) : '';
        const srcEntity = t.source_country === 'Ivory Coast' ? 'GMA' : 'GMD';
        const dstEntity = t.dest_country === 'Ivory Coast' ? 'GMA' : 'GMD';
        const desc = t.debit_desc || t.credit_desc || t.description || '-';
        html += '<tr>'
            + '<td>' + (BANK_DISPLAY[t.source_bank]||t.source_bank) + '</td>'
            + '<td style="font-family:monospace;font-size:11px;color:#4a5568;text-align:center">' + srcAcct + '</td>'
            + '<td style="font-weight:600;color:' + (srcEntity==='GMA' ? 'var(--primary)' : '#718096') + '">' + srcEntity + ' <span style="font-weight:400;font-size:11px;color:#718096">(' + t.source_country + ')</span></td>'
            + '<td>' + (BANK_DISPLAY[t.dest_bank]||t.dest_bank) + '</td>'
            + '<td style="font-family:monospace;font-size:11px;color:#4a5568;text-align:center">' + dstAcct + '</td>'
            + '<td style="font-weight:600;color:' + (dstEntity==='GMA' ? 'var(--primary)' : '#718096') + '">' + dstEntity + ' <span style="font-weight:400;font-size:11px;color:#718096">(' + t.dest_country + ')</span></td>'
            + '<td class="num">$' + t.amount_usd.toLocaleString('en-US', {{minimumFractionDigits:0}}) + '</td>'
            + '<td class="num">' + t.amount_xof.toLocaleString('en-US', {{maximumFractionDigits:0}}) + '</td>'
            + '<td style="white-space:nowrap;font-size:11px">' + (t.debit_date||'-') + '</td>'
            + '<td style="white-space:nowrap;font-size:11px">' + (t.credit_date||'-') + '</td>'
            + '<td class="num" style="font-size:11px">' + floatBadge(t.float_days) + '</td>'
            + '<td style="white-space:nowrap;font-size:11px;color:#6b46c1">' + (t.debit_value_date||'-') + '</td>'
            + '<td style="white-space:nowrap;font-size:11px;color:#6b46c1">' + (t.credit_value_date||'-') + '</td>'
            + '<td class="num" style="font-size:11px">' + floatBadge(t.value_float_days) + '</td>'
            + '<td title="' + desc.replace(/"/g,'&quot;') + '">' + desc + '</td>'
            + '</tr>';
    }}
    if (filtered.length === 0) html = '<tr><td colspan="15" style="text-align:center;padding:40px;color:#64748b;">No intercompany transfers match filters</td></tr>';
    document.getElementById('icBody').innerHTML = html;
    document.getElementById('icPageInfo').textContent = filtered.length === 0 ? 'No matches' : 'Showing ' + (start+1) + '-' + end + ' of ' + filtered.length;
    document.getElementById('icPrev').disabled = icPage === 0;
    document.getElementById('icNext').disabled = end >= filtered.length;
}}

function exportIntraCSV() {{
    const filtered = filterTF(INTRA_TF, 'intraFrom', 'intraTo', 'intraSearch');
    let csv = 'From_Bank,From_Account,To_Bank,To_Account,Amount_XOF,Amount_USD,Posted_Out,Posted_In,Post_Float,Value_Out,Value_In,Value_Float,Description,Debit_Ref,Credit_Ref\\n';
    filtered.forEach(t => {{
        csv += ['"'+(BANK_DISPLAY[t.source_bank]||t.source_bank)+'"',t.source_account,'"'+(BANK_DISPLAY[t.dest_bank]||t.dest_bank)+'"',t.dest_account,
            t.amount_xof,t.amount_usd,t.debit_date||'',t.credit_date||'',t.float_days===null?'':t.float_days,
            t.debit_value_date||'',t.credit_value_date||'',t.value_float_days===null?'':t.value_float_days,
            '"'+(t.debit_desc||t.description||'').replace(/"/g,"''")+'"',t.debit_ref,t.credit_ref].join(',')+'\\n';
    }});
    const blob = new Blob([csv], {{type:'text/csv'}});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = '{"gma" if GMA_MODE else "ctm"}_intra_transfers.csv'; a.click();
}}

function exportICCSV() {{
    const filtered = filterTF(IC_TF, 'icFrom', 'icTo', 'icSearch');
    let csv = 'From_Bank,From_Account,From_Entity,From_Country,To_Bank,To_Account,To_Entity,To_Country,Amount_XOF,Amount_USD,Posted_Out,Posted_In,Post_Float,Value_Out,Value_In,Value_Float,Description,Debit_Ref,Credit_Ref\\n';
    filtered.forEach(t => {{
        const srcE = t.source_country==='Ivory Coast'?'GMA':'GMD';
        const dstE = t.dest_country==='Ivory Coast'?'GMA':'GMD';
        csv += ['"'+(BANK_DISPLAY[t.source_bank]||t.source_bank)+'"',t.source_account,srcE,t.source_country,
            '"'+(BANK_DISPLAY[t.dest_bank]||t.dest_bank)+'"',t.dest_account,dstE,t.dest_country,
            t.amount_xof,t.amount_usd,t.debit_date||'',t.credit_date||'',t.float_days===null?'':t.float_days,
            t.debit_value_date||'',t.credit_value_date||'',t.value_float_days===null?'':t.value_float_days,
            '"'+(t.debit_desc||t.description||'').replace(/"/g,"''")+'"',t.debit_ref,t.credit_ref].join(',')+'\\n';
    }});
    const blob = new Blob([csv], {{type:'text/csv'}});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = '{"gma" if GMA_MODE else "ctm"}_intercompany_transfers.csv'; a.click();
}}

// Initial render
renderTxns();
renderIntra();
renderIC();
</script>
</body>
</html>"""

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML report generated: {OUTPUT_FILE}')
print(f'File size: {len(html)/1e6:.1f} MB')
