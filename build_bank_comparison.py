#!/usr/bin/env python3
"""Build Ivory Coast Bank Comparison Matrix HTML dashboard from Excel data."""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
with open(BASE_DIR / 'bank_comparison_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Bank names (short)
BANKS = ['SIB', 'BACI', 'AFG Bank', 'SGBCI', 'Citi CI', 'Stanbic CI', 'BOA CI', 'MTN MoMo']
BANK_FULL = [
    'SIB (Société Ivoirienne de Banque)',
    'Banque Atlantique CI (BACI)',
    'AFG Bank CI (AFG Holding)',
    'Societe Generale CI (SGBCI)',
    "Citi CI (Citibank Côte d'Ivoire)",
    'Standard Bank / Stanbic CI',
    'Bank of Africa CI (BOA CI)',
    'MTN Mobile Money (MoMo)'
]
# Light-on-dark accessible colors for bank accents
BANK_COLORS = ['#66bb6a', '#42a5f5', '#ff9800', '#ef5350', '#26a69a', '#7986cb', '#ab47bc', '#ffee58']

# Short labels for scorecard bars and nav tabs
SCORECARD_SHORT = {
    '1. OVERVIEW & RISK': 'Risk',
    '2. FX CAPABILITIES': 'FX',
    '3. CASH MANAGEMENT & PAYMENTS': 'Cash Mgmt',
    '4. RURAL & NATIONWIDE COLLECTIONS IN IVORY COAST': 'Rural Colls.',
    '5. TRADE FINANCE': 'Trade Fin.',
    '6. THIRD-PARTY BANK PARTNERS & ECOSYSTEM': 'Partners',
    '7. CORPORATE BANKING CAPABILITIES': 'Corp. Banking',
    '8. BOND ISSUANCE & CAPITAL MARKETS': 'Capital Mkt.',
    '9. NETWORK & PARTNERSHIPS': 'Network',
    '10. KEY WEAKNESSES & RISKS': 'Weaknesses',
    '11. OVERALL SUITABILITY SUMMARY': 'Overall',
}

# Parse categories and rows
categories = []
current_cat = None
for i, row in enumerate(data):
    if i < 4:
        continue
    col_a = row[0].strip() if row[0] else ''
    col_b = row[1].strip() if row[1] else ''
    if col_a and re.match(r'^\d+\.', col_a):
        current_cat = {'name': col_a, 'rows': []}
        categories.append(current_cat)
    elif col_b and current_cat is not None:
        vals = [row[j].strip() if row[j] else '' for j in range(2, 10)]
        current_cat['rows'].append({'criteria': col_b, 'values': vals})


def extract_rating(text):
    """Extract numeric rating from text like 'GOOD (4/5)' or '4/5'."""
    m = re.search(r'(\d+(?:\.\d+)?)/5', text)
    return float(m.group(1)) if m else None


def hm_class_for(rating):
    """Return heatmap CSS class using conventional rounding (not banker's)."""
    if rating >= 4.5:
        return 'hm-5'
    elif rating >= 3.5:
        return 'hm-4'
    elif rating >= 2.5:
        return 'hm-3'
    elif rating >= 1.5:
        return 'hm-2'
    return 'hm-1'


def rating_color(val):
    """Return color for a rating value with consistent thresholds."""
    if val >= 4.5:
        return '#00e676'
    elif val >= 4.0:
        return '#4fc3f7'
    elif val >= 3.0:
        return '#ffa726'
    return '#ef5350'


def get_rating_class(text):
    """Return CSS class based on assessment keywords."""
    t = text.upper()
    if any(w in t for w in ['EXCELLENT', 'BEST-IN-CLASS', 'BEST', 'LEADER', 'VERY STRONG', 'PREMIER']):
        return 'rating-excellent'
    elif any(w in t for w in ['GOOD', 'STRONG', 'COMPETITIVE', 'FULL']):
        return 'rating-good'
    elif any(w in t for w in ['ADEQUATE', 'MODERATE', 'FAIR', 'SOME', 'IN PROGRESS']):
        return 'rating-adequate'
    elif any(w in t for w in ['LIMITED', 'BASIC', 'LOW', 'NONE', 'NOT ', 'N/A', 'PARTIAL', 'NICHE', 'HIGHER']):
        return 'rating-limited'
    return ''


def get_cat_short(name):
    """Get short category name for display."""
    num = name.split('.')[0].strip()
    full_key = num + '. ' + name.split('.', 1)[1].split('(')[0].strip()
    return SCORECARD_SHORT.get(full_key, full_key)


def get_cat_medium(name):
    """Get medium-length category name for nav tabs (max 24 chars)."""
    s = name.split('.')[0].strip() + '. ' + name.split('.', 1)[1].split('(')[0].strip()
    return s if len(s) <= 24 else s[:22] + '..'


# Collect overall ratings from category summaries
rating_rows = {}
for cat in categories:
    for r in cat['rows']:
        crit = r['criteria'].lower()
        if 'overall rating' in crit or 'overall suitability' in crit or 'issuance rating' in crit or 'network rating' in crit:
            rating_rows[cat['name']] = r

# Also find the "suitability" rows in categories that lack explicit ratings
# FX: use "FX Pricing Assessment" row; Rural: use "Collections Suitability" row
SYNTH_RATING_MAP = {
    'BEST-IN-CLASS': 5.0, 'EXCELLENT': 5.0,
    'COMPETITIVE': 4.0, 'GOOD': 4.0, 'STRONG': 4.0, 'VERY STRONG': 4.5,
    'FAIR': 3.0, 'ADEQUATE': 3.0, 'MODERATE': 3.0,
    'UNCLEAR': 2.5,
    'LIMITED': 2.0, 'BASIC': 2.0, 'LOW': 2.0, 'LOW-MODERATE': 2.5,
    'NONE': 1.0, 'NOT APPLICABLE': 1.0, 'NOT SUITED': 1.0, 'N/A': 1.0,
    'NOT RECOMMENDED': 1.5,
}


def synthesize_rating(text):
    """Derive a numeric rating from qualitative assessment text."""
    t = text.upper()
    # Try explicit rating first
    r = extract_rating(text)
    if r is not None:
        return r
    # Match keywords in priority order
    for keyword in ['BEST-IN-CLASS', 'EXCELLENT', 'VERY STRONG', 'COMPETITIVE', 'GOOD', 'STRONG',
                     'FAIR', 'ADEQUATE', 'MODERATE', 'UNCLEAR', 'LOW-MODERATE',
                     'LIMITED', 'BASIC', 'LOW', 'NOT RECOMMENDED', 'NOT SUITED',
                     'NOT APPLICABLE', 'NONE', 'N/A']:
        if keyword in t:
            return SYNTH_RATING_MAP[keyword]
    return None


# Build synthetic ratings for categories without explicit "Overall Rating" rows
SYNTH_CRITERIA = {
    '2. FX CAPABILITIES (Critical for Large International Payments)': 'FX Pricing Assessment',
    '4. RURAL & NATIONWIDE COLLECTIONS IN IVORY COAST (Critical Use Case)': 'Collections Suitability for Rural Ivory Coast',
}
for cat in categories:
    if cat['name'] in SYNTH_CRITERIA and cat['name'] not in rating_rows:
        target_crit = SYNTH_CRITERIA[cat['name']]
        for r in cat['rows']:
            if target_crit.lower() in r['criteria'].lower():
                # Build a synthetic rating row
                synth_vals = []
                for v in r['values']:
                    sr = synthesize_rating(v)
                    synth_vals.append(f'{sr}/5' if sr else 'N/A')
                rating_rows[cat['name']] = {'criteria': f'{target_crit} (derived)', 'values': synth_vals}
                break

# Final overall ratings (from cat 11)
final_ratings = None
for cat in categories:
    for r in cat['rows']:
        if 'OVERALL RATING' in r['criteria'] and '/5' in r['criteria']:
            final_ratings = r

# Ordered list of categories for scorecard/heatmap
DISPLAY_CATS = [
    '2. FX CAPABILITIES (Critical for Large International Payments)',
    '3. CASH MANAGEMENT & PAYMENTS (Critical for International FX Payments)',
    '4. RURAL & NATIONWIDE COLLECTIONS IN IVORY COAST (Critical Use Case)',
    '5. TRADE FINANCE',
    '8. BOND ISSUANCE & CAPITAL MARKETS',
    '9. NETWORK & PARTNERSHIPS',
]

# Build scorecard data
scorecard = {b: {} for b in BANKS}
for cat_name in DISPLAY_CATS:
    if cat_name in rating_rows:
        r = rating_rows[cat_name]
        for j, bank in enumerate(BANKS):
            rating = extract_rating(r['values'][j])
            if rating is not None:
                scorecard[bank][cat_name] = rating
            else:
                scorecard[bank][cat_name] = None  # explicit N/A

# Extract final overall
for j, bank in enumerate(BANKS):
    if final_ratings:
        r = extract_rating(final_ratings['values'][j])
        if r:
            scorecard[bank]['Overall'] = r


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')


# Sort banks by overall score descending for scorecard
sorted_bank_indices = sorted(range(len(BANKS)), key=lambda j: scorecard[BANKS[j]].get('Overall', 0), reverse=True)

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ivory Coast Banking Partner Comparison Matrix</title>
<style>
:root {
    --bg: #0f1419;
    --surface: #1a1f2e;
    --surface2: #232839;
    --border: #2d3348;
    --text: #e4e6eb;
    --text-dim: #8b8fa3;
    --accent: #4fc3f7;
    --excellent: #00e676;
    --good: #4fc3f7;
    --adequate: #ffa726;
    --limited: #ef5350;
    --warning: #ff9800;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; font-feature-settings: 'tnum' 1; }
.container { max-width: 1800px; margin: 0 auto; padding: 20px; }

/* Header */
.header { background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%); border-radius: 16px; padding: 32px 40px; margin-bottom: 24px; }
.header h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
.header .subtitle { color: rgba(255,255,255,0.7); font-size: 14px; }

/* Two-level navigation */
.nav-primary { display: flex; gap: 4px; background: var(--surface); border-radius: 12px; padding: 4px; margin-bottom: 8px; }
.nav-secondary { display: flex; gap: 4px; background: var(--surface); border-radius: 12px; padding: 4px; margin-bottom: 24px; overflow-x: auto; scrollbar-width: thin; scrollbar-color: var(--border) transparent; }
.nav-primary button, .nav-secondary button { background: transparent; border: none; color: var(--text-dim); padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; white-space: nowrap; flex-shrink: 0; }
.nav-primary button:hover, .nav-secondary button:hover { background: var(--surface2); color: var(--text); }
.nav-primary button.active, .nav-secondary button.active { background: var(--accent); color: #000; font-weight: 600; }

/* Tab content */
.tab { display: none; }
.tab.active { display: block; }

/* Scorecard */
.scorecard-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; margin-bottom: 32px; }
.score-card { background: var(--surface); border-radius: 12px; padding: 20px; border: 1px solid var(--border); border-left: 4px solid var(--border); position: relative; }
.score-card .rank-badge { position: absolute; top: 12px; right: 14px; font-size: 12px; font-weight: 700; color: var(--text-dim); background: var(--surface2); border-radius: 6px; padding: 2px 8px; }
.score-card .bank-name { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: var(--text); }
.score-card .overall { font-size: 36px; font-weight: 700; margin-bottom: 4px; }
.score-card .star-label { font-size: 12px; color: var(--text-dim); margin-bottom: 12px; }
.score-card .complement-note { font-size: 11px; color: var(--warning); margin-top: 4px; }
.score-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.score-bar .label { font-size: 11px; color: var(--text-dim); width: 80px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.score-bar .bar-bg { flex: 1; height: 6px; background: var(--surface2); border-radius: 3px; overflow: hidden; }
.score-bar .bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.score-bar .val { font-size: 11px; font-weight: 600; width: 28px; text-align: right; flex-shrink: 0; }

/* Category comparison table */
.cat-header { font-size: 18px; font-weight: 700; padding: 16px 0 12px; border-bottom: 2px solid var(--accent); margin-bottom: 4px; }
.comp-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.comp-table th { background: var(--surface); padding: 10px 12px; text-align: left; font-weight: 600; position: sticky; top: 0; z-index: 2; border-bottom: 2px solid var(--border); white-space: nowrap; }
.comp-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; max-width: 240px; }
.comp-table tr:hover td { background: rgba(79, 195, 247, 0.05); }
.comp-table td.criteria { font-weight: 600; color: var(--accent); min-width: 180px; max-width: 200px; position: sticky; left: 0; background: var(--bg); z-index: 1; }
.rating-excellent { background: rgba(0, 230, 118, 0.1); }
.rating-good { background: rgba(79, 195, 247, 0.08); }
.rating-adequate { background: rgba(255, 167, 38, 0.08); }
.rating-limited { background: rgba(239, 83, 80, 0.08); }

/* Rating legend */
.rating-legend { display: flex; gap: 20px; padding: 10px 0 14px; font-size: 11px; color: var(--text-dim); align-items: center; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-swatch { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }

/* Recommendation section */
.rec-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.rec-card { background: var(--surface); border-radius: 12px; padding: 20px; border-left: 4px solid; }
.rec-card h4 { font-size: 14px; font-weight: 700; margin-bottom: 8px; color: var(--text); }
.rec-card p { font-size: 12px; color: var(--text-dim); }
.rec-card .rec-action { font-size: 13px; font-weight: 600; margin-top: 8px; }

/* Heatmap */
.heatmap-table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
.heatmap-table th, .heatmap-table td { padding: 12px 16px; text-align: center; font-size: 13px; }
.heatmap-table th { background: var(--surface); font-weight: 600; }
.heatmap-table td { border: 1px solid var(--border); }
.hm-5 { background: rgba(0,230,118,0.25); color: var(--excellent); font-weight: 700; }
.hm-4 { background: rgba(79,195,247,0.2); color: var(--good); font-weight: 600; }
.hm-3 { background: rgba(255,167,38,0.15); color: var(--adequate); }
.hm-2 { background: rgba(239,83,80,0.15); color: var(--limited); }
.hm-1 { background: rgba(239,83,80,0.25); color: var(--limited); font-weight: 600; }
.hm-na { color: var(--text-dim); }

/* Scrollable table wrapper */
.table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid var(--border); }

/* Finding cards — severity-tinted backgrounds */
.finding { border-radius: 10px; padding: 20px; margin-bottom: 16px; border-left: 4px solid var(--accent); }
.finding h4 { font-size: 15px; margin-bottom: 8px; }
.finding p { font-size: 13px; color: var(--text-dim); }
.finding .severity { font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 6px; }
.finding-critical { background: rgba(239, 83, 80, 0.06); border-left-color: var(--limited); }
.finding-high { background: rgba(255, 152, 0, 0.05); border-left-color: var(--warning); }
.finding-medium { background: var(--surface); border-left-color: var(--adequate); }
.finding-info { background: var(--surface); border-left-color: var(--good); }
.severity-critical { color: var(--limited); }
.severity-high { color: var(--warning); }
.severity-medium { color: var(--adequate); }
.severity-info { color: var(--good); }

.footer { text-align: center; padding: 32px 0; color: var(--text-dim); font-size: 12px; border-top: 1px solid var(--border); margin-top: 40px; }

/* Print stylesheet */
@media print {
    body { background: #fff; color: #000; }
    .nav-primary, .nav-secondary { display: none; }
    .tab { display: block !important; page-break-before: auto; }
    .header { background: #1a237e !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .score-card, .rec-card, .finding { break-inside: avoid; border-color: #ccc; }
    .score-card { background: #f8f9fa; }
    .comp-table td.criteria { background: #fff; }
    .table-wrap { overflow: visible; }
    .container { max-width: 100%; }
}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>Ivory Coast Banking Partner Comparison Matrix</h1>
    <div class="subtitle">Comprehensive Edition &mdash; 8 Banking Partners Evaluated Across 11 Categories | Prepared for Corporate Banking Evaluation | February 2026</div>
</div>

<div class="nav-primary">
    <button class="active" data-tab="scorecard" onclick="showTab('scorecard')">Scorecard</button>
    <button data-tab="heatmap" onclick="showTab('heatmap')">Heatmap</button>
    <button data-tab="findings" onclick="showTab('findings')">Key Findings</button>
    <button data-tab="recommendations" onclick="showTab('recommendations')">Recommendations</button>
</div>
<div class="nav-secondary">
'''

# Add category tabs with trimmed labels
for i, cat in enumerate(categories):
    nav_label = get_cat_medium(cat['name'])
    html += f'    <button data-tab="cat{i}" onclick="showTab(\'cat{i}\')">{esc(nav_label)}</button>\n'

html += '</div>\n\n'

# ── TAB: SCORECARD ──
html += '<div id="scorecard" class="tab active">\n'
html += '<h2 style="margin-bottom:20px;font-size:20px;">Overall Scorecard &mdash; Large FX + Rural Collections Use Case</h2>\n'
html += '<div class="scorecard-grid">\n'

for rank, j in enumerate(sorted_bank_indices, 1):
    bank = BANKS[j]
    overall = scorecard[bank].get('Overall', 0)
    color = BANK_COLORS[j]
    overall_color = rating_color(overall) if overall else '#ef5350'
    html += f'''<div class="score-card" style="border-left-color:{color}">
    <div class="rank-badge">#{rank}</div>
    <div class="bank-name">{esc(bank)}</div>
    <div class="overall" style="color:{overall_color}">{overall}</div>
    <div class="star-label">out of 5.0</div>
'''
    if bank == 'MTN MoMo':
        html += '    <div class="complement-note">Complement provider &mdash; not a full banking partner</div>\n'

    for cat_name in DISPLAY_CATS:
        short_label = get_cat_short(cat_name)
        val = scorecard[bank].get(cat_name)
        if val is None:
            html += f'''    <div class="score-bar">
        <div class="label" title="{esc(cat_name)}">{esc(short_label)}</div>
        <div class="bar-bg"><div class="bar-fill" style="width:0%;background:var(--border)"></div></div>
        <div class="val" style="color:var(--text-dim)">N/A</div>
    </div>
'''
        else:
            pct = val / 5 * 100
            bar_color = rating_color(val)
            html += f'''    <div class="score-bar">
        <div class="label" title="{esc(cat_name)}">{esc(short_label)}</div>
        <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
        <div class="val" style="color:{bar_color}">{val}</div>
    </div>
'''
    html += '</div>\n'

html += '</div>\n</div>\n\n'

# ── TAB: HEATMAP ──
html += '<div id="heatmap" class="tab">\n'
html += '<h2 style="margin-bottom:20px;font-size:20px;">Capability Heatmap</h2>\n'
html += '<div class="table-wrap"><table class="heatmap-table"><thead><tr><th>Category</th>'
for b in BANKS:
    html += f'<th>{esc(b)}</th>'
html += '</tr></thead><tbody>\n'

# Use DISPLAY_CATS order for heatmap rows
for cat_name in DISPLAY_CATS:
    if cat_name in rating_rows:
        r = rating_rows[cat_name]
        short = get_cat_short(cat_name)
        html += f'<tr><td style="text-align:left;font-weight:600">{esc(short)}</td>'
        for v in r['values']:
            rating = extract_rating(v)
            if rating is not None:
                hmc = hm_class_for(rating)
                html += f'<td class="{hmc}">{rating}/5</td>'
            else:
                html += '<td class="hm-na">N/A</td>'
        html += '</tr>\n'

# Add overall row
if final_ratings:
    html += '<tr style="border-top:3px solid var(--accent)"><td style="text-align:left;font-weight:700;color:var(--accent)">OVERALL</td>'
    for v in final_ratings['values']:
        rating = extract_rating(v)
        if rating is not None:
            hmc = hm_class_for(rating)
            html += f'<td class="{hmc}" style="font-size:16px">{rating}/5</td>'
        else:
            html += '<td class="hm-na">N/A</td>'
    html += '</tr>\n'

html += '</tbody></table></div>\n</div>\n\n'

# ── TAB: KEY FINDINGS ──
html += '<div id="findings" class="tab">\n'
html += '<h2 style="margin-bottom:20px;font-size:20px;">Key Findings &amp; Analysis</h2>\n'

findings = [
    ('CRITICAL', 'severity-critical', 'finding-critical', '&#x26A0;',
     'FX Capabilities: Clear Two-Tier Market',
     'Citi and Standard Bank dominate large FX — Citi led the FIRST ever FX hedging transaction in CI and handles "very large" flows with best-in-class pricing. SGBCI offers full SG Global Markets suite. SIB, BACI, AFG, and BOA have limited-to-no hedging capabilities. MTN MoMo has zero FX capability.'),
    ('CRITICAL', 'severity-critical', 'finding-critical', '&#x26A0;',
     'Rural Collections: Structural Gap for Global Banks',
     'Citi (1-2 offices, Abidjan only) and Standard Bank (1 office, Abidjan only) CANNOT handle rural collections. They must be paired with SIB (67+ branches, 21 cities) or SGBCI (66+ branches) for CI-wide coverage. SG\'s YUP agency banking was DISCONTINUED in March 2022, weakening their rural strategy.'),
    ('HIGH', 'severity-high', 'finding-high', '&#x26A0;',
     'SG Parent Exit Risk: Africa Divestment Trend',
     'Societe Generale sold subsidiaries in Ghana (2023) and Cameroon (2023). While CI remains a "strategic market," this divestment pattern is a monitored risk for companies building long-term banking relationships with SGBCI.'),
    ('HIGH', 'severity-high', 'finding-high', '&#x26A0;',
     'MTN MoMo: NOT a Licensed Bank',
     'MTN MoMo is regulated by ARTCI + BCEAO e-money rules but is NOT a BCEAO-licensed bank. No deposit insurance. Mobile wallet funds are not protected like bank deposits. Useful as a complement for last-mile mobile collections, but cannot be a standalone banking partner.'),
    ('HIGH', 'severity-high', 'finding-high', '&#x26A0;',
     'ISO 20022 Migration: Uneven Readiness',
     'Citi is a global ISO 20022 migration LEADER with camt.053 v8 available. Standard Bank and SGBCI are well-advanced. SIB, BACI, AFG, and BOA are "in progress" — aligning with BCEAO/SWIFT CBPR+ timeline but not yet fully migrated. Companies planning TMS integration should factor this gap.'),
    ('MEDIUM', 'severity-medium', 'finding-medium', '&#x25CF;',
     'AFG Bank CI: New Entity Risk',
     'Rebranded in 2023 from former Banque Atlantique subsidiary. Compliance track record still building. Unrated parent (private Ivorian group). Should be re-evaluated in 18 months. Not recommended for large FX or complex structured finance.'),
    ('MEDIUM', 'severity-medium', 'finding-medium', '&#x25CF;',
     'Trade Finance Concentration',
     'Citi is the LEAD bank for cocoa exporters in CI and arranged the country\'s debut Eurobond ($2.6B, 2014). For agri-commodity trade, Citi and Standard Bank are Tier 1. SIB and SGBCI are Tier 2. AFG and MTN have no trade finance capability.'),
    ('INFO', 'severity-info', 'finding-info', '&#x2139;',
     'Optimal Banking Structure Emerges',
     'For a company needing both large international FX payments AND nationwide CI collections, the data points to a two-bank strategy: Citi or Standard Bank (for FX/international/trade) + SIB (for domestic/rural collections). SGBCI is a strong all-around alternative but carries parent exit risk.'),
    ('INFO', 'severity-info', 'finding-info', '&#x2139;',
     'Digital Banking Maturity Hierarchy',
     'CitiDirect BE is best-in-class for treasury management. Standard Bank Business Online with Infosys Finacle is strong for API/ERP integration. SGBCI offers the only dedicated call center in CI. SIB\'s SIBNET and BACI/BOA platforms are functional but less sophisticated.'),
    ('INFO', 'severity-info', 'finding-info', '&#x2139;',
     'BCEAO Mobile Money Interoperability',
     'All licensed banks can receive Orange Money / MTN MoMo transfers via the BCEAO SICA-CI interbank platform. This framework enables any bank to accept mobile money collections — reducing the exclusive advantage of having a mobile money partnership.'),
]

for severity, sev_class, card_class, icon, title, desc in findings:
    html += f'''<div class="finding {card_class}">
    <div class="severity {sev_class}">{icon} {severity}</div>
    <h4>{esc(title)}</h4>
    <p>{esc(desc)}</p>
</div>
'''

html += '</div>\n\n'

# ── TAB: RECOMMENDATIONS ──
html += '<div id="recommendations" class="tab">\n'
html += '<h2 style="margin-bottom:20px;font-size:20px;">Banking Partner Recommendations</h2>\n'

# Action color tiers (6 distinct)
ACTION_COLORS = {
    'STRONGLY RECOMMEND': 'var(--excellent)',
    'STRONGLY CONSIDER': '#a3e635',
    'RECOMMEND': 'var(--good)',
    'CONSIDER': 'var(--adequate)',
    'EVALUATE': 'var(--warning)',
    'COMPLEMENT ONLY': 'var(--limited)',
}

recs = [
    ('Citi CI', BANK_COLORS[4], 'STRONGLY RECOMMEND',
     'Best for: International FX, SWIFT MT940/MT942, sovereign/institutional, cocoa trade finance.',
     'Limitation: Must pair with local bank for rural CI collections. Premium pricing not suited for SME volumes.'),
    ('Standard Bank / Stanbic', BANK_COLORS[5], 'STRONGLY RECOMMEND',
     'Best for: Pan-Africa CIB, multinationals with Africa-wide operations, structured/project finance, ICBC China partnership.',
     'Limitation: CIB-only, 1 Abidjan office. Must pair with SIB or SGBCI for domestic collections.'),
    ('SIB', BANK_COLORS[0], 'STRONGLY CONSIDER',
     'Best for: CI-wide hinterland collections (67+ branches, 21 cities), UEMOA agri-trade, local/regional corporates.',
     'Limitation: Limited FX hedging. Digital platform behind Citi/SG. Some public sector NPL exposure.'),
    ('SGBCI', BANK_COLORS[3], 'RECOMMEND',
     'Best for: Full-service corporate banking, structured finance, custody (SGSS Best Sub-Custodian 2025), only CI bank with call center.',
     'Risk: SG parent divesting Africa (Ghana/Cameroon 2023). YUP rural solution discontinued March 2022. Verify rural strategy.'),
    ('BACI', BANK_COLORS[1], 'CONSIDER',
     'Best for: Mid-size corporates, UEMOA regional payments, Atlantique Finance DCM/capital markets.',
     'Limitation: Limited rural presence. Basic FX hedging only. UEMOA concentration risk.'),
    ('BOA CI', BANK_COLORS[6], 'CONSIDER',
     'Best for: Commodity trade via BOA UK, pan-African BMCE operations, 19-country network.',
     'Limitation: Moderate digital maturity. Limited FX capability. BMCE integration ongoing.'),
    ('AFG Bank CI', BANK_COLORS[2], 'EVALUATE',
     'Best for: Local Ivorian relationships, digital-first SMEs, political/sovereignty banking considerations.',
     'Risk: New entity (2023). Unrated parent. Compliance track record building. Re-evaluate in 18 months.'),
    ('MTN MoMo', BANK_COLORS[7], 'COMPLEMENT ONLY',
     'Best for: Last-mile rural mobile collections, payroll to unbanked workers, agent network coverage.',
     'Critical: NOT a licensed bank. No BCEAO deposit protection. Must pair with SIB or SGBCI. Not for large FX or deposits.'),
]

html += '<div class="rec-grid">\n'
for name, color, action, best, limit in recs:
    action_color = ACTION_COLORS.get(action, 'var(--text)')
    html += f'''<div class="rec-card" style="border-left-color:{color}">
    <h4>{esc(name)}</h4>
    <div class="rec-action" style="color:{action_color}">{esc(action)}</div>
    <p style="margin-top:8px">{esc(best)}</p>
    <p style="margin-top:6px;color:var(--warning)">{esc(limit)}</p>
</div>
'''
html += '</div>\n\n'

# Optimal structure recommendation
html += '''<div style="background:var(--surface);border-radius:12px;padding:24px;margin-top:24px;border:2px solid var(--accent)">
<h3 style="color:var(--accent);margin-bottom:12px">Recommended Banking Structure &mdash; Large International FX + Rural Collections</h3>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px">
<div style="background:var(--surface2);border-radius:8px;padding:16px">
    <h4 style="color:var(--excellent);margin-bottom:8px">Primary International Bank</h4>
    <p style="font-size:14px;font-weight:600">Citi CI or Standard Bank</p>
    <p style="font-size:12px;color:var(--text-dim);margin-top:4px">FX dealing, SWIFT GPI, MT940/MT942, trade finance, cross-border payments, liquidity management, ERP/TMS integration</p>
</div>
<div style="background:var(--surface2);border-radius:8px;padding:16px">
    <h4 style="color:var(--good);margin-bottom:8px">Primary Local Bank</h4>
    <p style="font-size:14px;font-weight:600">SIB (Soci&eacute;t&eacute; Ivoirienne de Banque)</p>
    <p style="font-size:12px;color:var(--text-dim);margin-top:4px">Domestic collections (67+ branches, 21 cities), UEMOA payments, rural hinterland coverage, agri-finance, local XOF operations</p>
</div>
<div style="background:var(--surface2);border-radius:8px;padding:16px">
    <h4 style="color:var(--adequate);margin-bottom:8px">Optional: Full-Service Alternative</h4>
    <p style="font-size:14px;font-weight:600">SGBCI (if SG parent exit risk acceptable)</p>
    <p style="font-size:12px;color:var(--text-dim);margin-top:4px">Could replace SIB if custody (SGSS) or call center needed. Monitor SG Africa divestment strategy. Verify rural collection capability post-YUP.</p>
</div>
<div style="background:var(--surface2);border-radius:8px;padding:16px">
    <h4 style="color:var(--warning);margin-bottom:8px">Optional: Last-Mile Layer</h4>
    <p style="font-size:14px;font-weight:600">MTN MoMo (complement only)</p>
    <p style="font-size:12px;color:var(--text-dim);margin-top:4px">Mobile agent collections in deep rural areas where no bank branch exists. Pair with licensed bank (SIB) for fund consolidation.</p>
</div>
</div>
</div>
'''

html += '</div>\n\n'

# ── CATEGORY DETAIL TABS ──
LEGEND_HTML = '''<div class="rating-legend">
    <span class="legend-item"><span class="legend-swatch rating-excellent"></span> Excellent</span>
    <span class="legend-item"><span class="legend-swatch rating-good"></span> Good</span>
    <span class="legend-item"><span class="legend-swatch rating-adequate"></span> Adequate</span>
    <span class="legend-item"><span class="legend-swatch rating-limited"></span> Limited / None</span>
</div>
'''

for i, cat in enumerate(categories):
    html += f'<div id="cat{i}" class="tab">\n'
    html += f'<div class="cat-header">{esc(cat["name"])}</div>\n'
    html += LEGEND_HTML
    html += '<div class="table-wrap"><table class="comp-table"><thead><tr><th>Criteria</th>'
    for b in BANKS:
        html += f'<th>{esc(b)}</th>'
    html += '</tr></thead><tbody>\n'
    for r in cat['rows']:
        html += f'<tr><td class="criteria">{esc(r["criteria"])}</td>'
        for v in r['values']:
            rc = get_rating_class(v)
            html += f'<td class="{rc}">{esc(v)}</td>'
        html += '</tr>\n'
    html += '</tbody></table></div>\n</div>\n\n'

# Footer and script
html += '''<div class="footer">
    Ivory Coast Banking Partner Comparison Matrix &mdash; Comprehensive Edition | Sources: Bank Official Websites, Citi.com, StandardBank.com, BCEAO, Trade.gov, SG Africa | February 2026
</div>

</div>

<script>
function showTab(id) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-primary button, .nav-secondary button').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    document.querySelectorAll('[data-tab="' + id + '"]').forEach(b => b.classList.add('active'));
    history.replaceState(null, '', '#' + id);
}

window.addEventListener('DOMContentLoaded', () => {
    const hash = location.hash.slice(1);
    if (hash && document.getElementById(hash)) showTab(hash);
});
</script>
</body>
</html>'''

with open(BASE_DIR / 'ivory-coast-bank-comparison.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Generated ivory-coast-bank-comparison.html ({len(html):,} bytes)')
print(f'Categories: {len(categories)}')
for cat in categories:
    short = get_cat_short(cat['name'])
    has_rating = '(has rating)' if cat['name'] in rating_rows else '(no rating)'
    print(f'  {short}: {len(cat["rows"])} criteria {has_rating}')
print(f'Heatmap rows: {sum(1 for c in DISPLAY_CATS if c in rating_rows)} + overall')
