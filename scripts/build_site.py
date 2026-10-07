"""Build the static portfolio site (index, dashboard, cleaning, report) from the fictional data."""
import json
from pathlib import Path
import pandas as pd

base = Path(__file__).resolve().parent.parent
site = base
site.mkdir(exist_ok=True)

sales = pd.read_csv(base / "data" / "sales_fictional.csv")
raw = pd.read_csv(base / "data" / "survey_raw_fictional.csv", dtype=str, keep_default_na=False)
clean = pd.read_csv(base / "data" / "survey_clean.csv").astype({"age": "Int64"})
log = json.loads((base / "data" / "cleaning_log.json").read_text())

NAME = "Claudine Uwanyirigira"
CSS = """
:root{--bg:#fbfaf8;--fg:#1f2430;--muted:#5d6676;--card:#fff;--line:#e3e0da;--accent:#1f5c99;--accent2:#c2693a;--good:#2f7d4f}
@media (prefers-color-scheme:dark){:root{--bg:#14171d;--fg:#e8e8e6;--muted:#a3a9b5;--card:#1c2028;--line:#2d333d;--accent:#6aa8e6;--accent2:#e79a6e;--good:#6cc08c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:28px 16px 64px}
a{color:var(--accent)}h1{font-size:1.9rem;margin:.2em 0}h2{font-size:1.3rem;margin-top:1.8em}
.muted{color:var(--muted)}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.kpi b{display:block;font-size:1.6rem}.tag{display:inline-block;font-size:.75rem;border:1px solid var(--line);border-radius:99px;padding:1px 10px;margin-right:6px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}th{color:var(--muted);font-weight:600}
.note{font-size:.85rem;color:var(--muted);border-left:3px solid var(--accent2);padding-left:10px;margin:16px 0}
nav a{margin-right:14px}select{font:inherit;padding:6px 10px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg)}
.bad{color:var(--accent2)}.ok{color:var(--good)}
"""
NOTE = '<p class="note">All data on this page is <b>fictional</b>, generated for demonstration. It does not come from any employer or client.</p>'

def page(title, body, extra_head="", back=True):
    nav = '<nav><a href="index.html">&larr; Portfolio</a></nav>' if back else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style>{extra_head}</head><body><div class="wrap">{nav}{body}</div></body></html>"""

# ---------------- numbers used in the report (computed, never typed) ----------------
sales["profit"] = sales.revenue_rwf - sales.cost_rwf
tot_rev = sales.revenue_rwf.sum(); margin = sales.profit.sum() / tot_rev * 100
by_branch = sales.groupby("branch").agg(rev=("revenue_rwf", "sum"), prof=("profit", "sum")).sort_values("rev", ascending=False)
by_branch["share"] = by_branch.rev / tot_rev * 100; by_branch["margin"] = by_branch.prof / by_branch.rev * 100
by_cat = sales.groupby("category").revenue_rwf.sum().sort_values(ascending=False)
monthly = sales.groupby("month").revenue_rwf.sum()
MN = {"01":"January","02":"February","03":"March","04":"April","05":"May","06":"June","07":"July","08":"August","09":"September","10":"October","11":"November","12":"December"}
peak_m, low_m = (MN[monthly.idxmax()[5:]], MN[monthly.idxmin()[5:]])
dec_vs_nov = (monthly["2025-12"] / monthly["2025-11"] - 1) * 100
mm = lambda x: f"{x/1e6:.1f}M"

# ---------------- Dashboard ----------------
records = sales[["month", "branch", "category", "units_sold", "revenue_rwf", "cost_rwf"]].to_dict("records")
dash_body = f"""
<h1>Retail sales dashboard</h1>
<p class="muted">Problem solved: a small retailer's monthly Excel exports were hard to compare across branches; this gives revenue, margin and category mix in one view.</p>
{NOTE}
<label>Branch: <select id="branch"></select></label>
<div class="grid" style="margin-top:14px">
<div class="card kpi"><span class="muted">Revenue (RWF)</span><b id="k_rev"></b></div>
<div class="card kpi"><span class="muted">Gross margin</span><b id="k_mar"></b></div>
<div class="card kpi"><span class="muted">Units sold</span><b id="k_units"></b></div></div>
<div class="card"><h2 style="margin-top:0">Monthly revenue, 2025</h2><svg id="line" viewBox="0 0 720 260" width="100%" role="img" aria-label="Monthly revenue line chart"></svg></div>
<div class="card"><h2 style="margin-top:0">Revenue by category</h2><svg id="bars" viewBox="0 0 720 190" width="100%" role="img" aria-label="Revenue by category bar chart"></svg></div>
<script>
const D={json.dumps(records)};
const sel=document.getElementById('branch');
['All branches',...new Set(D.map(r=>r.branch))].forEach(b=>{{const o=document.createElement('option');o.textContent=b;sel.appendChild(o)}});
const fmt=n=>n.toLocaleString('en-US'),css=n=>getComputedStyle(document.documentElement).getPropertyValue(n);
function draw(){{
 const b=sel.value,rows=D.filter(r=>b==='All branches'||r.branch===b);
 const rev=rows.reduce((a,r)=>a+r.revenue_rwf,0),cost=rows.reduce((a,r)=>a+r.cost_rwf,0),u=rows.reduce((a,r)=>a+r.units_sold,0);
 k_rev.textContent=fmt(rev);k_mar.textContent=((rev-cost)/rev*100).toFixed(1)+'%';k_units.textContent=fmt(u);
 const months=[...new Set(D.map(r=>r.month))].sort(),mv=months.map(m=>rows.filter(r=>r.month===m).reduce((a,r)=>a+r.revenue_rwf,0));
 const raw=Math.max(...mv)*1.05/4,pw=Math.pow(10,Math.floor(Math.log10(raw))),step=[1,1.5,2,2.5,3,4,5,10].map(f=>f*pw).find(s=>s>=raw),mx=step*4,L=document.getElementById('line'),X=i=>60+i*(630/11),Y=v=>220-v/mx*190;
 let s='';for(let t=0;t<=4;t++){{const v=mx*t/4;s+=`<line x1="60" x2="690" y1="${{Y(v)}}" y2="${{Y(v)}}" stroke="${{css('--line')}}"/><text x="54" y="${{Y(v)+4}}" text-anchor="end" font-size="11" fill="${{css('--muted')}}">${{(v/1e6).toFixed(step>=1e6?1:2)}}M</text>`}}
 s+=`<polyline fill="none" stroke="${{css('--accent')}}" stroke-width="2.5" points="${{mv.map((v,i)=>X(i)+','+Y(v)).join(' ')}}"/>`;
 mv.forEach((v,i)=>{{s+=`<circle cx="${{X(i)}}" cy="${{Y(v)}}" r="3.5" fill="${{css('--accent')}}"><title>${{months[i]}}: ${{fmt(v)}} RWF</title></circle><text x="${{X(i)}}" y="242" text-anchor="middle" font-size="11" fill="${{css('--muted')}}">${{months[i].slice(5)}}</text>`}});
 L.innerHTML=s;
 const cats=[...new Set(D.map(r=>r.category))].map(c=>[c,rows.filter(r=>r.category===c).reduce((a,r)=>a+r.revenue_rwf,0)]).sort((a,b)=>b[1]-a[1]);
 const cm=Math.max(...cats.map(c=>c[1])),B=document.getElementById('bars');let t='';
 cats.forEach((c,i)=>{{const w=c[1]/cm*470;t+=`<text x="0" y="${{28+i*42}}" font-size="13" fill="${{css('--fg')}}">${{c[0]}}</text><rect x="120" y="${{12+i*42}}" width="${{w}}" height="22" rx="4" fill="${{css('--accent')}}"/><text x="${{126+w}}" y="${{28+i*42}}" font-size="12" fill="${{css('--muted')}}">${{(c[1]/1e6).toFixed(1)}}M</text>`}});
 B.innerHTML=t}}
sel.onchange=draw;draw();
</script>"""
(site / "dashboard.html").write_text(page("Retail sales dashboard", dash_body))

# ---------------- Cleaning before / after ----------------
r_in, r_out = len(raw), len(clean)
bad_age = raw[~raw.age.str.fullmatch(r"\d+")].age.str.strip()
before = raw.head(8).to_html(index=False, border=0)
after = clean.head(8).fillna("").to_html(index=False, border=0)
dist_before = raw.district.nunique(); dist_after = clean.district.nunique()
clean_body = f"""
<h1>Survey data cleaning: before and after</h1>
<p class="muted">Problem solved: a program's survey export had duplicates, mixed spellings and formats, and impossible values, so it could not be analyzed or reported on reliably.</p>
{NOTE}
<div class="grid">
<div class="card kpi"><span class="muted">Rows</span><b>{r_in} &rarr; {r_out}</b></div>
<div class="card kpi"><span class="muted">District spellings</span><b>{dist_before} &rarr; {dist_after}</b></div>
<div class="card kpi"><span class="muted">Duplicates removed</span><b>{log['duplicates_removed']}</b></div></div>
<h2>What was wrong, and the rule applied</h2>
<table><tr><th>Issue</th><th>Rule</th><th>Records affected</th></tr>
<tr><td>Duplicate respondents</td><td>Keep first record per respondent ID</td><td>{log['duplicates_removed']}</td></tr>
<tr><td>District typed as "GASABO ", "gasabo", etc.</td><td>Trim spaces, standardize capitalization</td><td>{dist_before} spellings &rarr; {dist_after}</td></tr>
<tr><td>Gender: F, female, M, blank</td><td>Map to Female / Male; blanks left missing, not guessed</td><td>{log['gender_missing']} missing</td></tr>
<tr><td>Attends school: Y, yes, YES, N</td><td>Map to Yes / No; blanks left missing</td><td>{log['attends_school_missing']} missing</td></tr>
<tr><td>Three date formats</td><td>Convert all to YYYY-MM-DD</td><td>{log['dates_unparsed']} unparsed</td></tr>
<tr><td>Ages like 0, 150, 999, "sixteen"</td><td>Valid range 10-19; outside range set to missing, flagged not invented</td><td>{log['age_out_of_range_set_missing']} out of range, {log['age_text_values_repaired_or_missing']} text values</td></tr>
<tr><td>Scores like 540, -20, "N/A"</td><td>Valid range 0-100; others set to missing</td><td>{log['score_out_of_range_set_missing']} out of range, {log['score_non_numeric_set_missing']} non-numeric</td></tr></table>
<p class="note">Principle: nothing is guessed. Invalid values become missing and are counted in a log, so the analyst knows exactly what was changed.</p>
<h2>Before (first 8 raw rows)</h2><div class="card" style="overflow-x:auto">{before}</div>
<h2>After (first 8 cleaned rows)</h2><div class="card" style="overflow-x:auto">{after}</div>
<p class="muted">Files: <a href="data/survey_raw_fictional.csv">raw CSV</a> &middot; <a href="data/survey_clean.csv">cleaned CSV</a> &middot; <a href="scripts/clean_survey.py">cleaning script (Python)</a></p>"""
(site / "cleaning.html").write_text(page("Survey data cleaning", clean_body))

# ---------------- Report ----------------
rows_b = "".join(f"<tr><td>{b}</td><td>{mm(r.rev)}</td><td>{r.share:.0f}%</td><td>{r.margin:.1f}%</td></tr>" for b, r in by_branch.iterrows())
top = by_branch.index[0]
rep_body = f"""
<h1>2025 sales performance: short analysis report</h1>
<p class="muted">Problem solved: the owner needs to know where revenue comes from and where to focus next year.</p>
{NOTE}
<h2>Summary</h2>
<p>The five branches generated <b>RWF {mm(tot_rev)}</b> in 2025 at a gross margin of <b>{margin:.1f}%</b>. {top} contributed the most revenue ({by_branch.loc[top,'share']:.0f}%). Groceries is the largest category ({by_cat.iloc[0]/tot_rev*100:.0f}% of revenue). Sales peaked in {peak_m} and were lowest in {low_m}, then rebounded in December.</p>
<h2>Findings</h2>
<p><b>1. Branch performance differs mainly in volume.</b> Margins are similar across branches (roughly {by_branch.margin.min():.0f}-{by_branch.margin.max():.0f}%), so the gap between branches comes from how much each one sells rather than how profitably.</p>
<div class="card"><table><tr><th>Branch</th><th>Revenue (RWF)</th><th>Share</th><th>Gross margin</th></tr>{rows_b}</table></div>
<p><b>2. Seasonality matters.</b> Revenue climbed from {mm(monthly.iloc[0])} in January to {mm(monthly.max())} in {peak_m}, fell to {mm(monthly.min())} in {low_m}, and December was {dec_vs_nov:.0f}% above November.</p>
<p><b>3. Category mix is concentrated.</b> Groceries and Household together account for {(by_cat['Groceries']+by_cat['Household'])/tot_rev*100:.0f}% of revenue, so stock availability in those two categories has the largest effect on results.</p>
<h2>Suggested next steps</h2>
<p>Review stock and staffing for the weaker months, test promotions for the lowest-revenue branches, and track margin by product within Groceries to confirm which items drive profit.</p>
<h2>Method and limits</h2>
<p>Monthly totals by branch and category (240 records), summed with Python. Gross margin = (revenue - cost) / revenue. The data is fictional and monthly, so this report cannot show product-level or customer-level patterns, and it does not test whether differences are statistically significant.</p>
<p class="muted">Data: <a href="data/sales_fictional.csv">sales CSV</a> &middot; <a href="dashboard.html">interactive dashboard</a></p>"""
(site / "report.html").write_text(page("2025 sales report", rep_body))

# ---------------- Index ----------------
idx = f"""
<h1>{NAME}</h1>
<p class="muted">Data scientist &middot; Kigali, Rwanda &middot; Power BI, Excel, SQL, Python, GIS</p>
<p>I turn messy data into clear dashboards and reports for small businesses and NGOs. These three samples use fictional data to show how I work.</p>
{NOTE}
<div class="card"><span class="tag">Dashboard</span><h2 style="margin:.3em 0"><a href="dashboard.html">Retail sales dashboard</a></h2>
<p>Problem solved: gives a retailer revenue, margin and category mix across branches in one interactive view instead of scattered monthly spreadsheets.</p></div>
<div class="card"><span class="tag">Data cleaning</span><h2 style="margin:.3em 0"><a href="cleaning.html">Survey data cleaning, before and after</a></h2>
<p>Problem solved: turns a messy survey export (duplicates, mixed formats, impossible values) into analysis-ready data with a log of every change.</p></div>
<div class="card"><span class="tag">Analysis report</span><h2 style="margin:.3em 0"><a href="report.html">2025 sales performance report</a></h2>
<p>Problem solved: explains where revenue comes from and where to focus next, in plain language for a non-technical owner.</p></div>
<h2>Contact</h2><p>Email: <a href="mailto:cuwanyirigira97@gmail.com">cuwanyirigira97@gmail.com</a> &middot; Phone: +250 784 800 084</p>"""
(site / "index.html").write_text(page(f"{NAME} - Data portfolio", idx, back=False))
print("built")
print(by_branch.round(1)); print("dec_vs_nov", round(dec_vs_nov, 1), "peak", peak_m, "low", low_m)
