import openpyxl
import re
import json
from collections import Counter, defaultdict
from datetime import datetime

# XOF/USD - XOF is pegged to EUR (655.957 XOF = 1 EUR)
# Using approximate rate: 1 USD ~ 605 XOF (as of early 2025)
XOF_PER_USD = 605.0

HEADERS = ['InputDate','PostedDate','AccountNumber','Account','Bank','AccountType','Date','TransRef','Currency','Amount','BAIType','Comment']

# Country mapping by bank name and account prefix
BANK_COUNTRY = {
    'Bank Atlantique IC': 'Ivory Coast',
    'BOA Ivory Coast': 'Ivory Coast',
    'SOCGEN Ivory Coast': 'Ivory Coast',
    'SIB (IVORIAN BANK)': 'Ivory Coast',
    'CITI IVORY COAST': 'Ivory Coast',
    'STANBIC IVORY COAST': 'Ivory Coast',
    'MTN Mobile FS CI': 'Ivory Coast',
    'BICIS Senegal': 'Senegal',
    'Bank Atlantique SN': 'Senegal',
    'C.B.A.O. Senegal': 'Senegal',
    'Bank Africa Senegal': 'Senegal',
    'SOCGEN SENEGAL BNK': 'Senegal',
    'Citi Senegal Bank': 'Senegal',
    'AFG BK': 'Ivory Coast',       # AFG operates in CI; account prefix CI confirms
    'BANQUE POPULAIRE': 'Ivory Coast',  # Banque Populaire de Cote d'Ivoire
}

def get_country(bank_name, account_number):
    """Determine country from bank name, fallback to account number prefix."""
    if bank_name in BANK_COUNTRY:
        return BANK_COUNTRY[bank_name]
    acct = str(account_number or '')
    if acct.startswith('CI'):
        return 'Ivory Coast'
    elif acct.startswith('SN'):
        return 'Senegal'
    return 'Unknown'

def parse_row(row):
    d = {}
    for i, h in enumerate(HEADERS):
        if i < len(row):
            d[h] = row[i]
        else:
            d[h] = None
    return d

def classify_comment(comment):
    if not comment:
        return 'Unclassified', '', ''

    comment = str(comment)
    fr = ''
    trid = ''
    py = ''
    bnf = ''

    if 'FR:' in comment:
        parts = comment.split('FR:')
        rest = parts[1] if len(parts) > 1 else ''
        for tag in ['ENDT:', 'TRID:', 'PY:', 'BNF:', 'GMA']:
            if tag in rest:
                idx = rest.index(tag)
                if not fr:
                    fr = rest[:idx].strip()
                rest = rest[idx:]
        if not fr:
            fr = rest.strip()
        if 'TRID:' in comment:
            trid = comment.split('TRID:')[1].split('PY:')[0].split('BNF:')[0].split('GMA')[0].strip()
        if 'PY:' in comment:
            py = comment.split('PY:')[1].split('BNF:')[0].split('GMA')[0].strip()
        if 'BNF:' in comment:
            bnf = comment.split('BNF:')[1].split('GMA')[0].strip()
    else:
        fr = comment.strip()

    description = py if py else fr
    fr_lower = fr.lower()

    if any(x in fr_lower for x in ['virement', 'vir.compense', 'vir int', 'vir emis', 'vir recu', 'virt ', 'transfer']):
        cat = 'Wire Transfer'
    elif any(x in fr_lower for x in ['cheque', 'chq', 'remise cheque']):
        cat = 'Check / Cheque'
    elif any(x in fr_lower for x in ['agios', 'interest', 'interet']):
        cat = 'Interest / Agios'
    elif any(x in fr_lower for x in ['commission', 'frais', 'fees', 'charges', 'com ']):
        cat = 'Fees / Commissions'
    elif any(x in fr_lower for x in ['tax amount', 'tva', 'impot', 'taxe']):
        cat = 'Tax'
    elif any(x in fr_lower for x in ['salary', 'salaire', 'paie', 'paye']):
        cat = 'Payroll / Salary'
    elif any(x in fr_lower for x in ['telex', 'swift']):
        cat = 'SWIFT / Telex'
    elif any(x in fr_lower for x in ['effet', 'traite', 'bill of exchange']):
        cat = 'Bills / Effets'
    elif any(x in fr_lower for x in ['balance requirement', 'debit chgs', 'number of debit', 'number of credit']):
        cat = 'Bank Charges'
    elif any(x in fr_lower for x in ['espece', 'retrait', 'versement', 'cash', 'caisse']):
        cat = 'Cash'
    elif any(x in fr_lower for x in ['prelevement', 'debit direct']):
        cat = 'Direct Debit'
    elif any(x in fr_lower for x in ['outward', 'inward']):
        cat = 'Cross-border'
    elif any(x in fr_lower for x in ['domiciliation', 'domic']):
        cat = 'Domiciliation'
    elif any(x in fr_lower for x in ['remise', 'encaissement']):
        cat = 'Collection / Remise'
    elif any(x in fr_lower for x in ['ordre de paiement', 'payment order']):
        cat = 'Payment Order'
    elif fr.strip() == '' or fr_lower in ['nonref', '']:
        cat = 'Unclassified'
    else:
        cat = 'Other'

    return cat, description[:80], bnf[:60]

def classify_flow(t, transfer_indices, idx):
    """Classify transaction into flow type: Collection, Payment, Inter-Account Transfer, Bank Costs, Payroll, Tax."""
    desc = (t.get('description') or '').lower()
    cat = t['category']
    amt = t['amount_xof']

    # --- BANK COSTS ---
    if cat in ['Fees / Commissions', 'Bank Charges', 'Interest / Agios', 'Direct Debit']:
        return 'Bank Costs'
    if cat == 'Tax':
        return 'Tax'

    # --- INTER-ACCOUNT TRANSFERS (keyword-based) ---
    if any(x in desc for x in ['virt inter', 'nivellement', 'appro compte', 'appro caisse',
                                 'transfert interne', 'vir boaweb fav grands', 'vir boaweb recu grands']):
        return 'Inter-Account Transfer'

    # --- INTER-ACCOUNT TRANSFERS (matched pairs) ---
    if idx in transfer_indices:
        if not any(x in desc for x in ['vir.recu:', 'virement recu de la compense',
                                         "virement d'ordre de", 'effet au']):
            return 'Inter-Account Transfer'

    # --- PAYROLL ---
    if cat == 'Payroll / Salary' or any(x in desc for x in ['paiement cnps']):
        return 'Payroll'

    # --- COLLECTIONS (credits from third parties) ---
    if amt > 0:
        return 'Collection'

    # --- PAYMENTS (debits to third parties) ---
    if amt < 0:
        return 'Payment'

    return 'Unclassified'

# Load all files
all_rows = []
files = [
    ('XOF transactions 1.xlsx', True),
    ('xof transactions.xlsx', False),
    ('XOF 2.xlsx', False),
    ('XOF 3.xlsx', False),
    ('xof 4.xlsx', False),
]

for fname, has_header in files:
    wb = openpyxl.load_workbook(fname, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if has_header and i == 0:
            continue
        d = parse_row(row)
        if d['Amount'] is None:
            continue
        try:
            amt = float(d['Amount'])
        except:
            continue

        cat, desc, bnf = classify_comment(d['Comment'])
        country = get_country(str(d['Bank'] or ''), str(d['AccountNumber'] or ''))

        posted = d['PostedDate']
        if isinstance(posted, datetime):
            date_str = posted.strftime('%Y-%m-%d')
            month_key = posted.strftime('%Y-%m')
        elif isinstance(posted, str):
            try:
                dt = datetime.strptime(posted, '%m/%d/%Y')
                date_str = dt.strftime('%Y-%m-%d')
                month_key = dt.strftime('%Y-%m')
            except:
                date_str = str(posted)
                month_key = 'Unknown'
        else:
            date_str = str(posted)
            month_key = 'Unknown'

        all_rows.append({
            'date': date_str,
            'month': month_key,
            'account': str(d['Account'] or ''),
            'bank': str(d['Bank'] or ''),
            'country': country,
            'account_type': str(d['AccountType'] or ''),
            'ref': str(d['TransRef'] or ''),
            'amount_xof': amt,
            'amount_usd': round(amt / XOF_PER_USD, 2),
            'category': cat,
            'description': desc,
            'beneficiary': bnf,
            'source': fname,
        })
    wb.close()
    print(f'Loaded {fname}')

print(f'\nTotal transactions: {len(all_rows):,}')

# --- Flow classification: find inter-account transfer pairs ---
by_date_amount = defaultdict(list)
for i, r in enumerate(all_rows):
    key = (r['date'], abs(r['amount_xof']))
    by_date_amount[key].append(i)

transfer_indices = set()
transfer_pairs = []  # List of (debit_idx, credit_idx) for Transfers tab
for key, indices in by_date_amount.items():
    if len(indices) < 2:
        continue
    debits = [(i, all_rows[i]) for i in indices if all_rows[i]['amount_xof'] < 0]
    credits = [(i, all_rows[i]) for i in indices if all_rows[i]['amount_xof'] > 0]
    if not debits or not credits:
        continue
    used_credits = set()
    for di, dt in debits:
        for ci, ct in credits:
            if ci in used_credits:
                continue
            if dt['account'] != ct['account']:
                transfer_indices.add(di)
                transfer_indices.add(ci)
                transfer_pairs.append((di, ci))
                used_credits.add(ci)
                break

# Apply flow classification to each transaction
for i, r in enumerate(all_rows):
    r['flow_type'] = classify_flow(r, transfer_indices, i)

# Aggregate stats
cat_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
bank_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
month_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})
country_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0, 'banks': set()})
flow_stats = defaultdict(lambda: {'count': 0, 'debit_xof': 0, 'credit_xof': 0})

for r in all_rows:
    for stats, key in [(cat_stats, r['category']), (bank_stats, r['bank']), (month_stats, r['month']), (flow_stats, r['flow_type'])]:
        stats[key]['count'] += 1
        if r['amount_xof'] < 0:
            stats[key]['debit_xof'] += r['amount_xof']
        else:
            stats[key]['credit_xof'] += r['amount_xof']
    # Country stats
    country_stats[r['country']]['count'] += 1
    country_stats[r['country']]['banks'].add(r['bank'])
    if r['amount_xof'] < 0:
        country_stats[r['country']]['debit_xof'] += r['amount_xof']
    else:
        country_stats[r['country']]['credit_xof'] += r['amount_xof']

all_rows.sort(key=lambda x: x['date'])

# Build transfer pairs data for Transfers tab
transfers_list = []
for di, ci in transfer_pairs:
    dt = all_rows[di]
    ct = all_rows[ci]
    transfers_list.append({
        'date': dt['date'],
        'source_bank': dt['bank'],
        'source_account': dt['account'],
        'source_country': dt['country'],
        'dest_bank': ct['bank'],
        'dest_account': ct['account'],
        'dest_country': ct['country'],
        'amount_xof': abs(dt['amount_xof']),
        'amount_usd': round(abs(dt['amount_xof']) / XOF_PER_USD, 2),
        'description': dt['description'] or ct['description'],
        'debit_ref': dt['ref'],
        'credit_ref': ct['ref'],
    })
transfers_list.sort(key=lambda x: x['date'])

print(f'Transfer pairs found: {len(transfers_list):,}')

# Convert country_stats sets to lists for JSON serialization
country_stats_json = {}
for k, v in sorted(country_stats.items(), key=lambda x: -x[1]['count']):
    country_stats_json[k] = {
        'count': v['count'],
        'debit_xof': v['debit_xof'],
        'credit_xof': v['credit_xof'],
        'banks': sorted(list(v['banks'])),
    }

output = {
    'rate': XOF_PER_USD,
    'total_count': len(all_rows),
    'category_stats': {k: v for k, v in sorted(cat_stats.items(), key=lambda x: -x[1]['count'])},
    'bank_stats': {k: v for k, v in sorted(bank_stats.items(), key=lambda x: -x[1]['count'])},
    'month_stats': {k: v for k, v in sorted(month_stats.items())},
    'country_stats': country_stats_json,
    'flow_stats': {k: v for k, v in sorted(flow_stats.items(), key=lambda x: -x[1]['count'])},
    'transfers': transfers_list,
    'transactions': all_rows,
}

with open('ctm_data.json', 'w') as f:
    json.dump(output, f)

print('Data exported to ctm_data.json')
print(f'\nCategory breakdown:')
for cat, s in sorted(cat_stats.items(), key=lambda x: -x[1]['count']):
    print(f"  {cat}: {s['count']:,} txns | Debits: {s['debit_xof']/1e6:,.1f}M XOF | Credits: {s['credit_xof']/1e6:,.1f}M XOF")

print(f'\nBank breakdown:')
for bank, s in sorted(bank_stats.items(), key=lambda x: -x[1]['count']):
    print(f"  {bank}: {s['count']:,} txns")

print(f'\nFlow type breakdown:')
for flow, s in sorted(flow_stats.items(), key=lambda x: -x[1]['count']):
    d = s['debit_xof']/1e6
    c = s['credit_xof']/1e6
    n = (s['debit_xof'] + s['credit_xof'])/1e6
    print(f"  {flow}: {s['count']:,} txns | Debits: {d:,.1f}M XOF | Credits: {c:,.1f}M XOF | Net: {n:,.1f}M XOF")
