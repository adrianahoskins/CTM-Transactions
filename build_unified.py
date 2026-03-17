#!/usr/bin/env python3
"""
Build unified GMA dashboard — merges:
  1. GMA Current State (from gma-current-state-ppt.html — built from PowerPoint)
  2. GMA Transactions (from ctm-gma-transactions.html)
  3. Rapid Assessment Gap Analysis (from gma-rapid-assessment-gap-analysis.html)
  4. CTM Executive Overview (generated from PowerPoint content)
  5. Bank Comparison Matrix (generated from Excel content)
into a single HTML file with top-level section navigation.
"""

import re
import sys
import os

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_body_content(html):
    """Extract content between <body> and </body> tags."""
    match = re.search(r'<body[^>]*>(.*)</body>', html, re.DOTALL)
    return match.group(1).strip() if match else ''

def extract_styles(html):
    """Extract all <style> blocks."""
    return re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)

def extract_scripts(html):
    """Extract all inline <script> blocks (not CDN refs)."""
    return re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.DOTALL)

def prefix_ids(html, prefix):
    """Prefix all id attributes and getElementById calls with a namespace."""
    # Prefix id="xxx" attributes
    html = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}{m.group(1)}"', html)
    # Prefix getElementById('xxx') calls
    html = re.sub(r"getElementById\('([^']+)'\)", lambda m: f"getElementById('{prefix}{m.group(1)}')", html)
    html = re.sub(r'getElementById\("([^"]+)"\)', lambda m: f'getElementById("{prefix}{m.group(1)}")', html)
    # Prefix showTab('xxx') calls in onclick
    html = re.sub(r"showTab\('([^']+)'\)", lambda m: f"showTab_{prefix.rstrip('-').replace('-','_')}('{prefix}{m.group(1)}')", html)
    # Prefix function showTab
    html = re.sub(r'function showTab\(', f"function showTab_{prefix.rstrip('-').replace('-','_')}(", html)
    return html

def build_ctm_executive_section():
    """Generate the CTM Executive Overview section from extracted PPT content."""
    return '''
<div class="kpi-row">
    <div class="kpi"><div class="label">Account Signers</div><div class="value">93</div></div>
    <div class="kpi"><div class="label">Bank Portals</div><div class="value">58</div></div>
    <div class="kpi"><div class="label">Portal Users</div><div class="value">181</div></div>
    <div class="kpi"><div class="label">Balance Visibility</div><div class="value" style="color:#276749;">91%</div></div>
    <div class="kpi"><div class="label">Signer Updates</div><div class="value">61</div></div>
    <div class="kpi"><div class="label">KYC Updates</div><div class="value">100</div></div>
    <div class="kpi"><div class="label">Access Points</div><div class="value">1,266</div></div>
    <div class="kpi"><div class="label">Portal User Updates</div><div class="value">100</div></div>
</div>

<div class="card">
    <div class="card-header">Key Objectives</div>
    <div class="card-body">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
            <div class="info-box">
                <h4>1. Liquidity Optimization</h4>
                <ul style="margin-left:16px; margin-top:4px; font-size:12px;">
                    <li>Ensure purposeful real-time visibility of cash across all entities and regions</li>
                    <li>Minimize idle balances and maximize returns through pooling or sweeping structures</li>
                </ul>
            </div>
            <div class="info-box">
                <h4>2. Cost Efficiency</h4>
                <ul style="margin-left:16px; margin-top:4px; font-size:12px;">
                    <li>Reduce banking fees, transaction costs, and FX conversion expenses</li>
                    <li>Rationalize bank accounts and relationships globally</li>
                </ul>
            </div>
            <div class="info-box">
                <h4>3. Standardization & Automation</h4>
                <ul style="margin-left:16px; margin-top:4px; font-size:12px;">
                    <li>Harmonize payment processes, approval workflows, and reporting globally</li>
                    <li>Deploy ION IT2 TMS and API/Host to Host integrations for automation</li>
                </ul>
            </div>
            <div class="info-box">
                <h4>4. Risk Management</h4>
                <ul style="margin-left:16px; margin-top:4px; font-size:12px;">
                    <li>Mitigate FX volatility, interest rate risk, and counterparty risk</li>
                    <li>Implement robust fraud prevention and cybersecurity measures</li>
                </ul>
            </div>
            <div class="info-box">
                <h4>5. Working Capital Efficiency</h4>
                <ul style="margin-left:16px; margin-top:4px; font-size:12px;">
                    <li>Optimize receivables, payables processes to free up cash</li>
                    <li>Align cash forecasting with operational cycles</li>
                </ul>
            </div>
            <div class="info-box">
                <h4>6. Regulatory Compliance</h4>
                <ul style="margin-left:16px; margin-top:4px; font-size:12px;">
                    <li>Adhere to local and international regulations (tax, FX, AML/KYC)</li>
                    <li>Maintain audit-ready processes and documentation</li>
                </ul>
            </div>
            <div class="info-box">
                <h4>7. Strategic Flexibility</h4>
                <ul style="margin-left:16px; margin-top:4px; font-size:12px;">
                    <li>Enable quick access to liquidity for acquisitions, expansions, or crisis response</li>
                    <li>Support global growth with scalable cash management infrastructure</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">Future State Systems Architecture</div>
    <div class="card-body">
        <div style="text-align:center; margin-bottom:20px;">
            <div style="display:inline-block; background:#1a365d; color:#fff; padding:12px 28px; border-radius:8px; font-weight:700; font-size:16px; margin-bottom:16px;">IT2 Anywhere — Central Payment Hub</div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:20px;">
            <div style="background:#ebf8ff; border:1px solid #bee3f8; border-radius:8px; padding:14px;">
                <h4 style="color:#2b6cb0; font-size:13px; margin-bottom:8px;">Outbound Payments</h4>
                <ul style="margin-left:14px; font-size:12px;">
                    <li>Wire file transmission</li>
                    <li>ACH file transmission</li>
                    <li>Check printing file</li>
                    <li>Payroll file</li>
                    <li>Virtual credit card file</li>
                </ul>
            </div>
            <div style="background:#f0fff4; border:1px solid #c6f6d5; border-radius:8px; padding:14px;">
                <h4 style="color:#276749; font-size:13px; margin-bottom:8px;">Controls & Screening</h4>
                <ul style="margin-left:14px; font-size:12px;">
                    <li>Sanctions screening service</li>
                    <li>Vendor verification file</li>
                    <li>Positive payee</li>
                    <li>ACK / NACKs</li>
                    <li>Payments STP</li>
                </ul>
            </div>
            <div style="background:#fffff0; border:1px solid #fefcbf; border-radius:8px; padding:14px;">
                <h4 style="color:#b7791f; font-size:13px; margin-bottom:8px;">Reporting & Reconciliation</h4>
                <ul style="margin-left:14px; font-size:12px;">
                    <li>Prior day / current day API</li>
                    <li>Balance & transactions</li>
                    <li>Payment status</li>
                    <li>Disbursement funding report</li>
                    <li>Monthly check recon file</li>
                </ul>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
            <div style="background:#fff5f5; border:1px solid #fed7d7; border-radius:8px; padding:14px;">
                <h4 style="color:#c53030; font-size:13px; margin-bottom:8px;">Citibank Conversion</h4>
                <ul style="margin-left:14px; font-size:12px;">
                    <li>Prior day reconciliation</li>
                    <li>Current day cash positioning</li>
                    <li>Entity report access</li>
                    <li>API call — repetitive code information for wires</li>
                </ul>
            </div>
            <div style="background:#faf5ff; border:1px solid #e9d8fd; border-radius:8px; padding:14px;">
                <h4 style="color:#6b46c1; font-size:13px; margin-bottom:8px;">BOA IREC (AR Automation)</h4>
                <ul style="margin-left:14px; font-size:12px;">
                    <li>Statement with incoming transactions</li>
                    <li>SFTP: AR information to bank</li>
                    <li>AR information from bank</li>
                    <li>Accounting entries</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">CTM Entities in Scope</div>
    <div class="card-body">
        <div style="display:flex; flex-wrap:wrap; gap:10px;">
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">LFMM</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">ZENITH</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">NMC</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">AGRICARE</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">FMOG</span>
            <span style="background:#1a365d; color:#fff; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700;">GMA &#9733;</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">PATIVOIRE</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">GMD</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">MOCHASA</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">BEIRA</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">IAG/UAG</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">NMG</span>
            <span style="background:#ebf8ff; border:1px solid #bee3f8; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">GMPN</span>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">Implementation Roadmap</div>
    <div class="card-body">
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0;">
            <div style="background:linear-gradient(135deg, #2c5282, #2b6cb0); color:#fff; padding:20px; border-radius:8px 0 0 8px; position:relative;">
                <div style="position:absolute; top:8px; right:12px; background:rgba(255,255,255,0.2); padding:2px 10px; border-radius:10px; font-size:11px;">Phase 1</div>
                <h4 style="font-size:15px; margin-bottom:4px;">ASSESS</h4>
                <p style="font-size:11px; opacity:0.85; margin-bottom:12px;">Rapid Assessment</p>
                <ul style="margin-left:14px; font-size:12px; line-height:1.8;">
                    <li>Banking footprint & rationalization</li>
                    <li>Blocker identification</li>
                    <li>Current and target process design</li>
                    <li>Current and proposed technology assessment</li>
                </ul>
                <div style="margin-top:14px; background:rgba(255,255,255,0.15); padding:6px 10px; border-radius:4px; font-size:11px;"><strong>Output:</strong> Approved design</div>
            </div>
            <div style="background:linear-gradient(135deg, #276749, #38a169); color:#fff; padding:20px; position:relative;">
                <div style="position:absolute; top:8px; right:12px; background:rgba(255,255,255,0.2); padding:2px 10px; border-radius:10px; font-size:11px;">Phase 2</div>
                <h4 style="font-size:15px; margin-bottom:4px;">IMPLEMENT</h4>
                <p style="font-size:11px; opacity:0.85; margin-bottom:12px;">Implementation</p>
                <ul style="margin-left:14px; font-size:12px; line-height:1.8;">
                    <li>Account rationalization</li>
                    <li>Payment & collections digitalization</li>
                    <li>Just-in-time funding</li>
                    <li>Just-in-time repatriation</li>
                    <li>AR automation & real-time visibility</li>
                </ul>
                <div style="margin-top:14px; background:rgba(255,255,255,0.15); padding:6px 10px; border-radius:4px; font-size:11px;"><strong>Output:</strong> Ivory Coast operational</div>
            </div>
            <div style="background:linear-gradient(135deg, #b7791f, #d69e2e); color:#fff; padding:20px; border-radius:0 8px 8px 0; position:relative;">
                <div style="position:absolute; top:8px; right:12px; background:rgba(255,255,255,0.2); padding:2px 10px; border-radius:10px; font-size:11px;">Phase 3</div>
                <h4 style="font-size:15px; margin-bottom:4px;">SCALE</h4>
                <p style="font-size:11px; opacity:0.85; margin-bottom:12px;">Scale & Optimize</p>
                <ul style="margin-left:14px; font-size:12px; line-height:1.8;">
                    <li>Wave 2 rollout</li>
                    <li>Receivables & operational dashboards</li>
                    <li>Policy & controls</li>
                    <li>Training & handoff</li>
                </ul>
                <div style="margin-top:14px; background:rgba(255,255,255,0.15); padding:6px 10px; border-radius:4px; font-size:11px;"><strong>Output:</strong> Senegal operational</div>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">TMS — IT2 & IT2 Anywhere</div>
    <div class="card-body">
        <div class="info-box">
            <h4>ION IT2 Treasury Management System</h4>
            <p style="margin-top:6px;">IT2 Anywhere is the cloud-hosted version of ION's IT2 TMS, providing centralized payment processing, sanctions screening, vendor verification, and real-time cash positioning across all CTM entities. Integrates with Citibank via API for current/prior day reporting and with BOA IREC for accounts receivable automation.</p>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">Accounts Receivable Application Automation</div>
    <div class="card-body">
        <div class="info-box">
            <h4>BOA Intelligent Receivables (IREC)</h4>
            <p style="margin-top:6px;">IREC automates AR matching and reconciliation. Incoming transaction statements from the bank are matched against AR data sent via SFTP. Matched and unmatched items are returned for review, with accounting entries generated automatically for posting to Business Central or ERP systems.</p>
        </div>
    </div>
</div>
'''

def build_bank_comparison_section():
    """Generate the Bank Comparison section from extracted Excel content."""
    return '''
<div class="kpi-row">
    <div class="kpi"><div class="label">Banks Evaluated</div><div class="value">8</div><div class="sub">+ MTN MoMo</div></div>
    <div class="kpi"><div class="label">Categories</div><div class="value">11</div><div class="sub">Across all dimensions</div></div>
    <div class="kpi"><div class="label">Top Rated (FX)</div><div class="value" style="font-size:16px;">Citi CI</div><div class="sub">4.5/5 — Best-in-class</div></div>
    <div class="kpi"><div class="label">Top Rated (Rural)</div><div class="value" style="font-size:16px;">SIB</div><div class="sub">67 branches, 21 cities</div></div>
</div>

<div class="card">
    <div class="card-header">Overall Suitability Ratings — For Large FX + Rural Collections Use Case</div>
    <div class="card-body" style="overflow-x:auto;">
        <table>
            <thead><tr><th>Bank</th><th>Rating</th><th>Best Suited For</th><th>Not Suited For</th><th>Key Risk</th><th>Recommendation</th></tr></thead>
            <tbody>
                <tr><td><strong>Citi CI</strong></td><td>4.5/5</td><td>Multinationals; sovereign-linked; trade-intensive; world-class FX + SWIFT GPI + MT940/MT942</td><td>Any company needing rural or semi-urban CI collections; SMEs below minimum threshold</td><td>LOW — Zero rural presence (MUST pair with local bank)</td><td><span style="background:#f0fff4; color:#276749; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">STRONGLY RECOMMEND (for FX)</span></td></tr>
                <tr><td><strong>SIB</strong></td><td>4/5</td><td>Large local/regional corps; UEMOA agri-trade; nationwide CI collection banking; cocoa/coffee campaign financing</td><td>World-class FX hedging; Eurobond access; CitiDirect-level portals</td><td>MODERATE — NPL exposure; digital maturity gap</td><td><span style="background:#f0fff4; color:#276749; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">STRONGLY CONSIDER</span></td></tr>
                <tr><td><strong>SocGen CI</strong></td><td>4/5</td><td>Multinationals; full-service corporate banking; structured finance; custody (SGSS Best 2025)</td><td>Companies that depended on YUP for rural; widest FX price competition</td><td>LOW-MOD — Parent exit risk (SG Africa divestments); YUP discontinued</td><td><span style="background:#f0fff4; color:#276749; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">RECOMMEND</span></td></tr>
                <tr><td><strong>Standard Bank</strong></td><td>4.5/5</td><td>Multinationals with Africa-wide CIB; structured + project finance; 5+ African country needs</td><td>Retail banking; rural collections; consumer payments; broad CI branch coverage</td><td>LOW — Small CI footprint; CIB only; newer brand</td><td><span style="background:#ebf8ff; color:#2b6cb0; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">RECOMMEND (Pan-Africa CIB)</span></td></tr>
                <tr><td><strong>BOA CI</strong></td><td>3.5/5</td><td>Mid-large corps; commodity trade; pan-African BMCE operations; BOA UK international commodity</td><td>Best-in-class FX; treasury portals; rural CI collections</td><td>MODERATE — BMCE integration; smaller balance sheet</td><td><span style="background:#fffff0; color:#b7791f; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">CONSIDER</span></td></tr>
                <tr><td><strong>Banque Atlantique</strong></td><td>3.5/5</td><td>Mid-size corporates; UEMOA regional payments; digital-first; local IB via Atlantique Finance</td><td>Deep rural CI collections; sophisticated FX hedging</td><td>MODERATE — UEMOA concentration; limited rural</td><td><span style="background:#fffff0; color:#b7791f; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">CONSIDER</span></td></tr>
                <tr><td><strong>AFG Bank CI</strong></td><td>3/5</td><td>SMEs; digital-first CI companies; local sovereign/political relationships; Ivorian-owned bank</td><td>Large FX; complex structured finance; rural collections</td><td>HIGHER — New entity (2023); limited track record; compliance maturing</td><td><span style="background:#fffff0; color:#b7791f; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">EVALUATE</span></td></tr>
                <tr><td><strong>MTN MoMo</strong></td><td>3/5</td><td>Consumer/SME mobile payments; payroll to unbanked; last-mile rural collections; agricultural corridors</td><td>Any company needing a licensed bank; large FX; bonds; regulated deposits</td><td>HIGHER — NOT a bank; no BCEAO protection; AML standards differ</td><td><span style="background:#fff5f5; color:#c53030; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">COMPLEMENT ONLY</span></td></tr>
            </tbody>
        </table>
        <div style="font-size:10px; color:#718096; margin-top:8px; font-style:italic;">Source: Ivory Coast Banking Partner Comparison Matrix — Comprehensive Edition, February 2026</div>
    </div>
</div>

<div class="card">
    <div class="card-header">FX Capabilities Comparison</div>
    <div class="card-body" style="overflow-x:auto;">
        <table>
            <thead><tr><th>Bank</th><th>FX Spot</th><th>Forwards/Options/Hedging</th><th>XOF/EUR Peg Expertise</th><th>Transaction Size</th><th>Pricing</th><th>Platform</th></tr></thead>
            <tbody>
                <tr><td><strong>Citi CI</strong></td><td>140+ currencies incl XOF/EUR/USD/GBP/CHF/JPY</td><td>FULL — First FX hedge in CI; NDF, options, structured</td><td>VERY STRONG — BCEAO correspondent; sovereign FX ops</td><td>VERY LARGE — No limit; best at $1M+</td><td>BEST-IN-CLASS — 0.1-0.5% on $1M+</td><td>CitiFX Pulse 24/7; CitiDirect BE</td></tr>
                <tr><td><strong>SocGen CI</strong></td><td>Full desk: XOF/EUR/USD/GBP/JPY+</td><td>FULL — SG Global Markets suite</td><td>STRONG — 60+ years CI FX history</td><td>LARGE — $50M+ competitive</td><td>COMPETITIVE — Below local avg for large</td><td>SG Markets digital; phone</td></tr>
                <tr><td><strong>Standard Bank</strong></td><td>Real-time via Business Online</td><td>FULL — Spot/forward/swap/options; Africa specialist</td><td>GOOD — CI branch has good understanding</td><td>LARGE — $10M+ competitive</td><td>COMPETITIVE</td><td>Business Online real-time; voice</td></tr>
                <tr><td><strong>SIB</strong></td><td>XOF/EUR/USD primary; GBP limited</td><td>LIMITED — Forwards via Attijariwafa; no complex derivatives</td><td>STRONG — Core UEMOA zone bank</td><td>MEDIUM — Up to ~$5M</td><td>FAIR — 0.5-1.5% on USD/XOF</td><td>SIBNET; phone for large FX</td></tr>
                <tr><td><strong>BOA CI</strong></td><td>Standard XOF/EUR/USD</td><td>LIMITED — Basic forwards only</td><td>ADEQUATE — Standard UEMOA ops</td><td>SMALL-MEDIUM</td><td>FAIR — Standard market</td><td>Business Online; phone</td></tr>
                <tr><td><strong>Atlantique</strong></td><td>Standard XOF/EUR/USD via BCP</td><td>SOME — Basic hedging via BCP; limited options</td><td>STRONG — Pan-UEMOA; all 8 countries</td><td>MEDIUM</td><td>FAIR — Standard UEMOA</td><td>Business Online; branch</td></tr>
                <tr><td><strong>AFG Bank</strong></td><td>Basic spot; limited range</td><td>BASIC ONLY — Not suited for hedging</td><td>ADEQUATE — UEMOA zone operator</td><td>SMALL-MEDIUM</td><td>UNCLEAR — Limited data</td><td>AFG e-Bank; branch</td></tr>
                <tr><td><strong>MTN MoMo</strong></td><td colspan="6" style="text-align:center; color:#718096;">No corporate FX capability — XOF mobile only</td></tr>
            </tbody>
        </table>
    </div>
</div>

<div class="card">
    <div class="card-header">Cash Management & Technology</div>
    <div class="card-body" style="overflow-x:auto;">
        <table>
            <thead><tr><th>Bank</th><th>Digital Platform</th><th>ERP/TMS Integration</th><th>SWIFT GPI</th><th>MT940/MT942</th><th>ISO 20022/camt</th><th>SWIFT BIC</th><th>Cash Mgmt Rating</th></tr></thead>
            <tbody>
                <tr><td><strong>Citi CI</strong></td><td>CitiDirect BE — World-class; 24/7 global</td><td>EXCELLENT — CitiConnect API; H2H; SAP/Oracle/Kyriba native; full STP</td><td>Founding member; UETR; same-day 100+ currencies</td><td>BEST — MT940+MT942+camt.053 v2/v8; multi-acct single file</td><td>LEADER — camt.053 v8; pacs.004; CBPR+</td><td>CITICIBA</td><td>EXCELLENT (5/5)</td></tr>
                <tr><td><strong>SocGen CI</strong></td><td>SG Digital — app+web; only CI bank with call center</td><td>GOOD — SWIFT FileAct; H2H</td><td>Full GPI via SG Group</td><td>YES — MT940+MT942 via SG SWIFT</td><td>GOOD — camt.053/052; FINplus ready</td><td>SGCICIABXXX</td><td>GOOD (4/5)</td></tr>
                <tr><td><strong>Standard Bank</strong></td><td>Business Online — 24/7; API/ERP; Finacle</td><td>GOOD — API Marketplace; ISO 20022; ERP integration</td><td>Full GPI; 20-country Africa</td><td>YES — via Business Online + SWIFT</td><td>GOOD — Finacle supports MX messages</td><td>SBICCIAB</td><td>GOOD (4/5)</td></tr>
                <tr><td><strong>SIB</strong></td><td>SIBNET — 24/7 web banking</td><td>LIMITED — Basic file export/import</td><td>GPI via Attijariwafa</td><td>YES — via SIBNET + SWIFT</td><td>IN PROGRESS — CBPR+ aligning</td><td>SIBCCIAB</td><td>GOOD (4/5)</td></tr>
                <tr><td><strong>BOA CI</strong></td><td>Business Online — web + mobile</td><td>BASIC — Standard file formats</td><td>GPI via BMCE/BOA SWIFT</td><td>YES — via SWIFT</td><td>IN PROGRESS — BMCE Group</td><td>BOACCIAB</td><td>ADEQUATE (3/5)</td></tr>
                <tr><td><strong>Atlantique</strong></td><td>Business Online — 24/7 web + mobile</td><td>LIMITED — Standard SWIFT formats</td><td>GPI via BCP Group</td><td>YES — via SWIFT</td><td>IN PROGRESS — BCP aligning</td><td>BACIABBB</td><td>ADEQUATE (3/5)</td></tr>
                <tr><td><strong>AFG Bank</strong></td><td>AFG e-Bank — digital-first; 24/7 app+web</td><td>BASIC — Limited ERP connectors</td><td>GPI compliant</td><td>YES — via SWIFT</td><td>IN PROGRESS — Early stage</td><td>AFGBCIAB</td><td>ADEQUATE (3/5)</td></tr>
                <tr><td><strong>MTN MoMo</strong></td><td>MoMo App + USSD</td><td>NONE</td><td>N/A</td><td>NO</td><td>N/A</td><td>N/A</td><td>ADEQUATE (3/5)</td></tr>
            </tbody>
        </table>
    </div>
</div>

<div class="card">
    <div class="card-header">Rural & Nationwide Collections</div>
    <div class="card-body" style="overflow-x:auto;">
        <table>
            <thead><tr><th>Bank</th><th>Branches in CI</th><th>Beyond Abidjan</th><th>Rural Access</th><th>Agent Banking</th><th>Mobile Money Integration</th><th>Rural Rating</th><th>Strategy</th></tr></thead>
            <tbody>
                <tr><td><strong>SIB</strong></td><td>67+ in 21 cities</td><td>GOOD — San Pedro, Bouake, Korhogo, Yamoussoukro, Daloa, Man+</td><td>MODERATE — Cocoa/coffee belt; gap for deep rural</td><td>LIMITED</td><td>MODERATE — BCEAO interop</td><td>MODERATE</td><td style="font-weight:600; color:#276749;">PRIMARY for hinterland + combine with MTN MoMo</td></tr>
                <tr><td><strong>SocGen CI</strong></td><td>66+ branches</td><td>GOOD — Abidjan + key cities</td><td>LOW-MOD — YUP DISCONTINUED Mar 2022</td><td>YUP shut down</td><td>MODERATE — BCEAO interop</td><td>LOW-MOD</td><td>Urban/semi-urban only; limited rural post-YUP</td></tr>
                <tr><td><strong>BOA CI</strong></td><td>39 branches</td><td>MODERATE — Some secondary cities</td><td>MODERATE — Limited true rural</td><td>LIMITED</td><td>MODERATE</td><td>LOW-MOD</td><td>Not primary rural bank</td></tr>
                <tr><td><strong>Atlantique</strong></td><td>~40-50 branches</td><td>MODERATE — Major cities</td><td>LIMITED — Urban/peri-urban</td><td>LIMITED</td><td>MODERATE</td><td>LOW-MOD</td><td>Not for deep rural</td></tr>
                <tr><td><strong>AFG Bank</strong></td><td>~20-25 branches</td><td>LIMITED — Abidjan focused</td><td>LIMITED — Urban focused</td><td>LIMITED</td><td>MODERATE</td><td>LOW</td><td>Not recommended for rural</td></tr>
                <tr><td><strong>Citi CI</strong></td><td>1-2 offices</td><td>NONE — Abidjan only</td><td>NONE</td><td>NONE</td><td>LIMITED</td><td>NONE</td><td style="color:#c53030;">Cannot collect — pair with SIB</td></tr>
                <tr><td><strong>Standard Bank</strong></td><td>1 office</td><td>NONE — Abidjan only</td><td>NONE</td><td>NONE</td><td>LIMITED</td><td>NONE</td><td style="color:#c53030;">Cannot collect — pair with SIB</td></tr>
                <tr><td><strong>MTN MoMo</strong></td><td>NONE (agents)</td><td>GOOD (mobile) — USSD + agents</td><td>STRONG — Best last-mile; any phone/network</td><td>EXCELLENT — Nationwide agents</td><td>CORE — interop with all BCEAO banks</td><td>STRONG</td><td style="font-weight:600; color:#276749;">COMPLEMENT for last-mile rural</td></tr>
            </tbody>
        </table>
    </div>
</div>

<div class="card">
    <div class="card-header">Trade Finance</div>
    <div class="card-body" style="overflow-x:auto;">
        <table>
            <thead><tr><th>Bank</th><th>Letters of Credit</th><th>Bank Guarantees/SBLC</th><th>Commodity/Agri Trade</th><th>Supply Chain Finance</th><th>Trade Fees vs Benchmark</th><th>Overall Rating</th></tr></thead>
            <tbody>
                <tr><td><strong>Citi CI</strong></td><td>World-class; globally confirmed 100+ countries</td><td>Full suite; Citi-confirmed SBLCs accepted globally</td><td>EXCELLENT — LEAD bank for cocoa exporters</td><td>EXCELLENT — Full SCF; reverse factoring</td><td>BEST — Below 1% for $10M+</td><td>EXCELLENT (5/5)</td></tr>
                <tr><td><strong>SIB</strong></td><td>Full import/export LC; Attijariwafa network</td><td>Standby LC; performance bonds</td><td>Active in cocoa/coffee campaign financing annually</td><td>Basic SCF via Attijariwafa</td><td>AVERAGE — ~1-2%</td><td>GOOD (4/5)</td></tr>
                <tr><td><strong>SocGen CI</strong></td><td>Full LC; SG global trade network</td><td>Full suite; SG global confirming</td><td>SG commodity trade finance; cocoa sector</td><td>SG Group SCF platform</td><td>AVERAGE/BELOW — ~1-1.5% large</td><td>GOOD (4/5)</td></tr>
                <tr><td><strong>Standard Bank</strong></td><td>Full LC in 13 currencies; Africa-wide commodity</td><td>Full suite; CIB specialty</td><td>Africa-wide commodity; mining + agri</td><td>Standard Bank SCF solutions</td><td>AVERAGE — ~1-2%</td><td>GOOD (4/5)</td></tr>
                <tr><td><strong>BOA CI</strong></td><td>Full LC; BOA UK specialist commodity trade</td><td>Full guarantees</td><td>BOA UK agri/commodity specialist</td><td>Limited SCF</td><td>AVERAGE — ~1-2%</td><td>GOOD (3.5/5)</td></tr>
                <tr><td><strong>Atlantique</strong></td><td>Full LC; BCP confirmation network</td><td>Full guarantee suite</td><td>Active in agri across UEMOA</td><td>SCF via BCP Group</td><td>AVERAGE — ~1-2%</td><td>ADEQUATE (3/5)</td></tr>
                <tr><td><strong>AFG Bank</strong></td><td>Basic LC; limited network</td><td>Basic guarantees</td><td>LIMITED — Early stage</td><td>LIMITED</td><td>ABOVE AVG — ~2-3%</td><td>LIMITED (2/5)</td></tr>
            </tbody>
        </table>
    </div>
</div>

<div class="card">
    <div class="card-header">Key Risks & Weaknesses</div>
    <div class="card-body" style="overflow-x:auto;">
        <table>
            <thead><tr><th>Bank</th><th>Weakness #1</th><th>Weakness #2</th><th>FX-Specific Weakness</th><th>Key Risk Level</th></tr></thead>
            <tbody>
                <tr><td><strong>Citi CI</strong></td><td>NO local presence for collections — single Abidjan office</td><td>High minimum thresholds — premium pricing; not for smaller corps</td><td>XOF liquidity — single office = less day-to-day XOF vs SG/SIB</td><td style="color:#276749;">LOW</td></tr>
                <tr><td><strong>SIB</strong></td><td>NPL exposure — public sector portfolio risk</td><td>Digital maturity — SIBNET behind CitiDirect/SG</td><td>Limited hedging — no options or structured FX</td><td style="color:#b7791f;">MODERATE</td></tr>
                <tr><td><strong>SocGen CI</strong></td><td style="color:#c53030; font-weight:600;">PARENT EXIT RISK — SG sold Ghana & Cameroon (2023)</td><td>YUP DISCONTINUED — rural gap since March 2022</td><td>Good but not Citi-level pricing for very large USD/EUR</td><td style="color:#b7791f;">LOW-MOD</td></tr>
                <tr><td><strong>Standard Bank</strong></td><td>LIMITED CI footprint — CIB only; 1 office</td><td>Recent entrant — only since 2017; shorter relationships</td><td>CI FX capability less proven than SG/Citi</td><td style="color:#276749;">LOW</td></tr>
                <tr><td><strong>BOA CI</strong></td><td>Smaller balance sheet — less capacity for large structured</td><td>Moderate digital maturity vs top-tier</td><td>Not suitable as primary FX bank</td><td style="color:#b7791f;">MODERATE</td></tr>
                <tr><td><strong>Atlantique</strong></td><td>UEMOA concentration — limited diversification</td><td>Less differentiated FX — basic forwards only</td><td>Limited hedging; not for complex programmes</td><td style="color:#b7791f;">MODERATE</td></tr>
                <tr><td><strong>AFG Bank</strong></td><td style="color:#c53030; font-weight:600;">NEW ENTITY RISK — rebranded 2023; compliance maturing</td><td>Small balance sheet — limited capacity</td><td>VERY LIMITED — not for large FX</td><td style="color:#c53030;">HIGHER</td></tr>
                <tr><td><strong>MTN MoMo</strong></td><td style="color:#c53030; font-weight:600;">NOT A LICENSED BANK — no BCEAO deposit protection</td><td>AML/KYC standards differ from banks</td><td>NO corporate FX</td><td style="color:#c53030;">HIGHER</td></tr>
            </tbody>
        </table>
        <div style="font-size:10px; color:#718096; margin-top:12px; font-style:italic;">Sources: Bank official websites, Citi.com, StandardBank.com, BCEAO, Trade.gov, SG Africa. Specific fee schedules unavailable publicly — direct quotes required. All data as of February 2026.</div>
    </div>
</div>
'''

def main():
    base = os.path.dirname(os.path.abspath(__file__))

    # Read source files
    print("Reading source files...")
    gap_html = read_file(os.path.join(base, 'gma-rapid-assessment-gap-analysis.html'))
    txn_html = read_file(os.path.join(base, 'ctm-gma-transactions.html'))
    cs_html = read_file(os.path.join(base, 'gma-current-state-ppt.html'))

    # Extract body content from each
    print("Extracting content...")
    gap_body = extract_body_content(gap_html)
    txn_body = extract_body_content(txn_html)
    cs_body = extract_body_content(cs_html)

    # Prefix IDs to avoid conflicts
    print("Namespacing sections...")
    gap_body = prefix_ids(gap_body, 'gap-')
    txn_body = prefix_ids(txn_body, 'txn-')
    cs_body = prefix_ids(cs_body, 'cs-')

    # Extract scripts for Chart.js initialization
    gap_scripts = extract_scripts(gap_html)
    txn_scripts = extract_scripts(txn_html)
    cs_scripts = extract_scripts(cs_html)

    # Namespace the scripts too
    gap_scripts_ns = [prefix_ids(s, 'gap-') for s in gap_scripts]
    txn_scripts_ns = [prefix_ids(s, 'txn-') for s in txn_scripts]
    cs_scripts_ns = [prefix_ids(s, 'cs-') for s in cs_scripts]

    # Remove script tags from body content (we'll add them back at the end)
    gap_body = re.sub(r'<script(?![^>]*src=)[^>]*>.*?</script>', '', gap_body, flags=re.DOTALL)
    txn_body = re.sub(r'<script(?![^>]*src=)[^>]*>.*?</script>', '', txn_body, flags=re.DOTALL)
    cs_body = re.sub(r'<script(?![^>]*src=)[^>]*>.*?</script>', '', cs_body, flags=re.DOTALL)

    # Remove the individual headers from each section (we'll use unified header)
    gap_body = re.sub(r'<div class="header">.*?</div>\s*', '', gap_body, count=1, flags=re.DOTALL)
    txn_body = re.sub(r'<div class="header">.*?</div>\s*', '', txn_body, count=1, flags=re.DOTALL)
    cs_body = re.sub(r'<div class="header">.*?</div>\s*', '', cs_body, count=1, flags=re.DOTALL)

    # Build CTM Executive and Bank Comparison sections
    ctm_exec = build_ctm_executive_section()
    bank_comp = build_bank_comparison_section()

    print("Building unified HTML...")

    unified = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GMA — Les Grands Moulins d'Abidjan | Unified Dashboard</title>
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
    --green: #276749;
    --green-bg: #f0fff4;
    --green-border: #c6f6d5;
    --red: #c53030;
    --red-bg: #fff5f5;
    --red-border: #fed7d7;
    --amber: #b7791f;
    --amber-bg: #fffff0;
    --amber-border: #fefcbf;
    --blue-bg: #ebf8ff;
    --blue-border: #bee3f8;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:var(--bg); color:var(--text); font-size:14px; line-height:1.6; }}
.main-header {{ background:linear-gradient(135deg, #0d1b2a, var(--primary)); color:#fff; padding:20px 32px; position:sticky; top:0; z-index:100; box-shadow:0 2px 8px rgba(0,0,0,0.2); }}
.main-header h1 {{ font-size:20px; font-weight:700; }}
.main-header .sub {{ font-size:12px; opacity:0.8; margin-top:2px; }}
.main-nav {{ display:flex; gap:4px; margin-top:12px; flex-wrap:wrap; }}
.main-nav button {{ padding:8px 18px; background:rgba(255,255,255,0.12); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:6px; cursor:pointer; font-size:12px; font-weight:500; transition:all 0.2s; }}
.main-nav button:hover {{ background:rgba(255,255,255,0.2); }}
.main-nav button.active {{ background:#fff; color:var(--primary); font-weight:700; border-color:#fff; }}
.section {{ display:none; }}
.section.active {{ display:block; }}
.section-header {{ background:linear-gradient(135deg, var(--primary), var(--primary-light)); color:#fff; padding:18px 32px; margin-bottom:0; }}
.section-header h2 {{ font-size:18px; font-weight:600; }}
.section-header .sub {{ font-size:12px; opacity:0.85; margin-top:2px; }}
.header {{ background:linear-gradient(135deg, var(--primary), var(--primary-light)); color:#fff; padding:18px 32px; }}
.header h1 {{ font-size:18px; font-weight:600; }}
.header .sub {{ font-size:12px; opacity:0.85; margin-top:2px; }}
.container {{ max-width:1440px; margin:0 auto; padding:20px; }}
.tabs {{ display:flex; gap:2px; background:var(--border); border-radius:8px 8px 0 0; padding:4px 4px 0; overflow-x:auto; flex-wrap:nowrap; }}
.tab {{ padding:10px 14px; cursor:pointer; background:#e2e8f0; border-radius:6px 6px 0 0; font-size:12px; font-weight:500; white-space:nowrap; border:none; color:var(--text); position:relative; }}
.tab:hover {{ background:#cbd5e0; }}
.tab.active {{ background:var(--card-bg); color:var(--primary); font-weight:600; }}
.tab .badge {{ position:absolute; top:2px; right:4px; width:8px; height:8px; border-radius:50%; }}
.tab .badge.green {{ background:#48bb78; }}
.tab .badge.amber {{ background:#ecc94b; }}
.tab .badge.red {{ background:#fc8181; }}
.tab-content {{ display:none; padding:20px 0; }}
.tab-content.active {{ display:block; }}
.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(160px,1fr)); gap:16px; margin-bottom:24px; }}
.kpi {{ background:var(--card-bg); border-radius:8px; padding:18px; box-shadow:0 1px 3px rgba(0,0,0,0.08); text-align:center; }}
.kpi .label {{ font-size:11px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-light); margin-bottom:4px; }}
.kpi .value {{ font-size:24px; font-weight:700; color:var(--primary); }}
.kpi .sub {{ font-size:11px; color:var(--text-light); margin-top:2px; }}
.card {{ background:var(--card-bg); border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:20px; overflow:hidden; }}
.card-header {{ background:var(--bg); padding:12px 16px; font-weight:600; font-size:14px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; }}
.card-body {{ padding:16px; }}
.table-wrap {{ overflow-x:auto; }}
.scroll-table {{ max-height:500px; overflow-y:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:var(--primary); color:#fff; padding:8px 12px; text-align:left; font-size:12px; position:sticky; top:0; z-index:1; cursor:pointer; white-space:nowrap; }}
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
.badge-info {{ display:inline-block; padding:2px 8px; background:#ebf8ff; color:#2b6cb0; border-radius:10px; font-size:11px; font-weight:600; }}
tfoot td {{ font-weight:700; background:#f7fafc; border-top:2px solid var(--primary); }}
.back-btn {{ display:none; margin-bottom:12px; padding:6px 14px; background:var(--primary); color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:12px; }}
.back-btn:hover {{ background:var(--primary-light); }}
.empty-state {{ text-align:center; padding:60px 20px; color:var(--text-light); }}
.progress-bar {{ height:6px; background:#e2e8f0; border-radius:3px; overflow:hidden; margin:8px 0; }}
.progress-fill {{ height:100%; border-radius:3px; transition:width 0.3s; }}
.progress-fill.high {{ background:#48bb78; }}
.progress-fill.mid {{ background:#ecc94b; }}
.progress-fill.low {{ background:#fc8181; }}
.status {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; }}
.status-complete {{ background:var(--green-bg); color:var(--green); border:1px solid var(--green-border); }}
.status-partial {{ background:var(--amber-bg); color:var(--amber); border:1px solid var(--amber-border); }}
.status-gap {{ background:var(--red-bg); color:var(--red); border:1px solid var(--red-border); }}
.evidence-list, .gap-list {{ list-style:none; padding:0; }}
.evidence-list li, .gap-list li {{ padding:8px 12px; border-bottom:1px solid var(--border); font-size:13px; display:flex; gap:8px; align-items:flex-start; }}
.evidence-list li:last-child, .gap-list li:last-child {{ border-bottom:none; }}
.evidence-list li::before {{ content:"\\2713"; color:var(--green); font-weight:700; flex-shrink:0; }}
.gap-list li::before {{ content:"\\2717"; color:var(--red); font-weight:700; flex-shrink:0; }}
.gap-list li.moderate::before {{ content:"\\26A0"; color:var(--amber); }}
.gap-list li.minor::before {{ content:"\\25CB"; color:var(--text-light); }}
.sev {{ display:inline-block; padding:1px 6px; border-radius:3px; font-size:10px; font-weight:700; margin-right:4px; }}
.sev-critical {{ background:#c53030; color:#fff; }}
.sev-major {{ background:#e53e3e; color:#fff; }}
.sev-moderate {{ background:#d69e2e; color:#fff; }}
.sev-minor {{ background:#a0aec0; color:#fff; }}
.exec-bar {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; margin-bottom:24px; }}
.exec-stat {{ background:var(--card-bg); border-radius:8px; padding:18px; box-shadow:0 1px 3px rgba(0,0,0,0.08); text-align:center; }}
.exec-stat .label {{ font-size:11px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-light); margin-bottom:4px; }}
.exec-stat .value {{ font-size:28px; font-weight:700; }}
.exec-stat .sub {{ font-size:11px; color:var(--text-light); margin-top:2px; }}
.two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
.section-title {{ font-size:16px; font-weight:600; color:var(--primary); margin:16px 0 10px; padding-bottom:6px; border-bottom:2px solid var(--primary); }}
.info-box {{ background:var(--blue-bg); border:1px solid var(--blue-border); border-radius:6px; padding:14px 18px; margin-bottom:14px; }}
.info-box h4 {{ color:#2b6cb0; font-size:13px; margin-bottom:6px; }}
.info-box p, .info-box li {{ font-size:12px; }}
.tbd-box {{ background:var(--amber-bg); border:1px solid var(--amber-border); border-radius:6px; padding:14px 18px; margin-bottom:14px; }}
.tbd-box h4 {{ color:var(--amber); font-size:13px; margin-bottom:6px; }}
.tbd-box p, .tbd-box li {{ font-size:12px; color:#744210; }}
.tbd-box ul {{ margin-left:16px; margin-top:4px; }}
.gap-box {{ background:var(--red-bg); border:1px solid var(--red-border); border-radius:6px; padding:14px 18px; margin-bottom:14px; }}
.gap-box h4 {{ color:var(--debit); font-size:13px; margin-bottom:6px; }}
.gap-box p, .gap-box li {{ font-size:12px; color:#742a2a; }}
.source-tag {{ font-size:10px; color:var(--text-light); font-style:italic; margin-top:4px; }}
@media (max-width:900px) {{
    .two-col {{ grid-template-columns:1fr; }}
    .exec-bar {{ grid-template-columns:1fr 1fr; }}
    .kpi-row {{ grid-template-columns:1fr 1fr; }}
    .main-header {{ padding:12px 16px; }}
    .main-nav button {{ padding:6px 12px; font-size:11px; }}
}}
</style>
</head>
<body>

<div class="main-header">
    <h1>GMA — Les Grands Moulins d'Abidjan</h1>
    <div class="sub">Ivory Coast | Unified Dashboard | Current State + Transactions + Gap Analysis + CTM Executive + Bank Comparison | March 2026</div>
    <div class="main-nav">
        <button class="active" onclick="showSection('sec-current-state')">Current State</button>
        <button onclick="showSection('sec-transactions')">Transactions</button>
        <button onclick="showSection('sec-gap-analysis')">Gap Analysis</button>
        <button onclick="showSection('sec-ctm-executive')">CTM Executive</button>
        <button onclick="showSection('sec-bank-comparison')">Bank Comparison</button>
    </div>
</div>

<!-- ==================== CURRENT STATE ==================== -->
<div id="sec-current-state" class="section active">
    <div class="section-header">
        <h2>Current State</h2>
        <div class="sub">Corporate Treasury | Converted from GMA Current State PowerPoint (60 slides) | March 2026</div>
    </div>
    {cs_body}
</div>

<!-- ==================== TRANSACTIONS ==================== -->
<div id="sec-transactions" class="section">
    <div class="section-header">
        <h2>XOF Transactions (USD Equivalent)</h2>
        <div class="sub">2023-11 to 2025-12 | 39,728 transactions | 10 bank accounts | 8 banks</div>
    </div>
    {txn_body}
</div>

<!-- ==================== GAP ANALYSIS ==================== -->
<div id="sec-gap-analysis" class="section">
    <div class="section-header">
        <h2>Rapid Assessment — Gap Analysis</h2>
        <div class="sub">Based on GMA Current State PPT (59 slides) + Transaction Data + CTM Executive + Bank Comparison Matrix | March 2026</div>
    </div>
    {gap_body}
</div>

<!-- ==================== CTM EXECUTIVE ==================== -->
<div id="sec-ctm-executive" class="section">
    <div class="section-header">
        <h2>CTM Executive Overview</h2>
        <div class="sub">Cash Management Transformation Project | 2026 | Source: CTM Executive Presentation (March 12)</div>
    </div>
    <div class="container">
        {ctm_exec}
    </div>
</div>

<!-- ==================== BANK COMPARISON ==================== -->
<div id="sec-bank-comparison" class="section">
    <div class="section-header">
        <h2>Ivory Coast Bank Comparison Matrix</h2>
        <div class="sub">Comprehensive Edition | 8 Banks + MTN MoMo | For Large International FX Payments + Nationwide Collections | February 2026</div>
    </div>
    <div class="container">
        {bank_comp}
    </div>
</div>

<script>
// Top-level section navigation
function showSection(id) {{
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.main-nav button').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
    window.scrollTo(0, 0);
    // Trigger chart resize for visible section
    setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
}}
</script>

<script>
// === Current State section scripts ===
{"".join(cs_scripts_ns)}
</script>

<script>
// === Transactions section scripts ===
{"".join(txn_scripts_ns)}
</script>

<script>
// === Gap Analysis section scripts ===
{"".join(gap_scripts_ns)}
</script>

</body>
</html>'''

    out_path = os.path.join(base, 'gma-unified-dashboard.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(unified)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Done! Output: {out_path} ({size_mb:.1f} MB)")

if __name__ == '__main__':
    main()
