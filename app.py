"""
Pow Wow Fuel Reconciliation — Command Center Dashboard
Dark mode • Floating widgets • Donut gauges • Trend charts
Computes all derived values in Python — does not rely on Excel formula cache.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
import os

st.set_page_config(
    page_title="Pow Wow Fuel Reconciliation",
    page_icon="GAS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Password Protection ──
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("""
        <style>
            .stApp { background-color: #0D1117; }
            #MainMenu, footer, header { visibility: hidden; }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 60vh;">
            <div style="background: #161B22; border: 1px solid #30363D; border-radius: 16px; 
                 padding: 40px; text-align: center; width: 400px;">
                <div style="font-size: 32px; margin-bottom: 16px;">GAS</div>
                <div style="font-size: 20px; font-weight: 700; color: #E6EDF3; margin-bottom: 8px;">
                    POW WOW FUEL RECONCILIATION
                </div>
                <div style="font-size: 12px; color: #484F58; margin-bottom: 24px;">
                    Enter password to access the dashboard
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            password = st.text_input("Password", type="password", key="pw_input")
            if st.button("Access Dashboard", use_container_width=True):
                if password == "PowWow2026":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

# ── Dark Mode CSS ──
st.markdown("""
<style>
    .stApp { background-color: #0D1117; color: #E6EDF3; }
    #MainMenu, footer, header { visibility: hidden; }
    
    .metric-card {
        background: #161B22; border: 1px solid #30363D; border-radius: 12px;
        padding: 20px 16px 16px 16px; text-align: center; position: relative; overflow: hidden;
    }
    .metric-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    }
    .metric-card.blue::before { background: #58A6FF; }
    .metric-card.green::before { background: #3FB950; }
    .metric-card.red::before { background: #F85149; }
    .metric-card.amber::before { background: #D29922; }
    .metric-card.purple::before { background: #A371F7; }
    .metric-card.cyan::before { background: #39D2C0; }
    .metric-card.orange::before { background: #DB6D28; }
    
    .metric-card .label {
        font-size: 11px; font-weight: 600; color: #8B949E;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
    }
    .metric-card .value { font-size: 28px; font-weight: 700; color: #E6EDF3; line-height: 1.2; }
    .metric-card .subtext { font-size: 11px; color: #484F58; margin-top: 4px; }
    
    .metric-card.alert-red { 
        background: linear-gradient(135deg, #161B22 0%, #2D1215 100%); border-color: #F85149;
    }
    .metric-card.alert-red .value { color: #F85149; }
    .metric-card.alert-amber {
        background: linear-gradient(135deg, #161B22 0%, #2D2410 100%); border-color: #D29922;
    }
    .metric-card.alert-amber .value { color: #D29922; }
    .metric-card.alert-green {
        background: linear-gradient(135deg, #161B22 0%, #0D2818 100%); border-color: #3FB950;
    }
    .metric-card.alert-green .value { color: #3FB950; }
    
    .section-header {
        font-size: 14px; font-weight: 600; color: #8B949E;
        text-transform: uppercase; letter-spacing: 2px;
        margin: 24px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #21262D;
    }
    
    .title-bar {
        background: linear-gradient(135deg, #161B22 0%, #1A2332 100%);
        border: 1px solid #30363D; border-radius: 16px;
        padding: 24px 32px; margin-bottom: 24px;
    }
    .title-bar h1 { font-size: 32px; font-weight: 700; color: #E6EDF3; margin: 0; }
    .title-bar .subtitle { font-size: 14px; color: #484F58; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──
# Cloud deployment: read from CSV if data/ directory exists
from pathlib import Path
DATA_DIR = Path(__file__).parent / 'data'
IS_CLOUD = DATA_DIR.exists() and (DATA_DIR / 'daily_recon.csv').exists()

WORKBOOK_PATH = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "Pow Wow Fuel Reconciliation.xlsx")

@st.cache_data(ttl=30)
def load_data():
    try:
        # Read raw data only — input columns, NOT formula columns
        dr_raw = pd.read_csv(DATA_DIR / 'daily_recon.csv') if IS_CLOUD else pd.read_excel(WORKBOOK_PATH, sheet_name='Daily Recon', header=1)
        dr_raw.columns = [str(c).strip().replace('\n', ' ') for c in dr_raw.columns]
        
        # Map to clean names based on column position (A=0, B=1, etc.)
        # New layout: A=Date, B=Meter Sales, C=Inv Sales, D=Sales Diff(formula), 
        # E=Meter Gal, F=Inv Gal, G=Gal Diff(formula), H=Gas CC, I=Fuel Cost, 
        # J=Fuel Profit, K=Margin(formula), L=Sales Match(formula), M=Gallon Match(formula), N=Notes
        cols = dr_raw.columns.tolist()
        rename = {}
        if len(cols) >= 14:
            rename = {
                cols[0]: 'Date', cols[1]: 'Meter_Sales', cols[2]: 'Invoice_Sales',
                cols[3]: 'Sales_Diff', cols[4]: 'Meter_Gallons', cols[5]: 'Invoice_Gallons',
                cols[6]: 'Gallon_Diff', cols[7]: 'Gas_CC', cols[8]: 'Fuel_Cost',
                cols[9]: 'Fuel_Profit', cols[10]: 'Margin_Per_Gallon',
                cols[11]: 'Sales_Match', cols[12]: 'Gallon_Match', cols[13]: 'Notes',
            }
        dr = dr_raw.rename(columns=rename)
        dr = dr[dr['Date'].notna()].copy()
        
        # COMPUTE all derived values in Python (don't rely on Excel formulas)
        dr['Meter_Sales'] = pd.to_numeric(dr['Meter_Sales'], errors='coerce')
        dr['Invoice_Sales'] = pd.to_numeric(dr['Invoice_Sales'], errors='coerce')
        dr['Meter_Gallons'] = pd.to_numeric(dr['Meter_Gallons'], errors='coerce')
        dr['Invoice_Gallons'] = pd.to_numeric(dr['Invoice_Gallons'], errors='coerce')
        dr['Gas_CC'] = pd.to_numeric(dr['Gas_CC'], errors='coerce')
        dr['Fuel_Cost'] = pd.to_numeric(dr['Fuel_Cost'], errors='coerce')
        dr['Fuel_Profit'] = pd.to_numeric(dr['Fuel_Profit'], errors='coerce')
        
        # Calculate derived columns
        dr['Sales_Diff'] = dr['Invoice_Sales'] - dr['Meter_Sales']
        dr['Gallon_Diff'] = dr['Invoice_Gallons'] - dr['Meter_Gallons']
        dr['Margin_Per_Gallon'] = np.where(
            (dr['Invoice_Gallons'].notna()) & (dr['Invoice_Gallons'] != 0),
            dr['Fuel_Profit'] / dr['Invoice_Gallons'], np.nan
        )
        dr['Sales_Match'] = np.where(
            dr['Meter_Sales'].isna() | dr['Invoice_Sales'].isna(), '',
            np.where(abs(dr['Meter_Sales'] - dr['Invoice_Sales']) <= 0.01, 'MATCH', 'MISMATCH')
        )
        # Gallon tolerance: 1.0 gallon (invoice rounds to whole numbers)
        dr['Gallon_Match'] = np.where(
            dr['Meter_Gallons'].isna() | dr['Invoice_Gallons'].isna(), '',
            np.where(abs(dr['Meter_Gallons'] - dr['Invoice_Gallons']) <= 1.0, 'MATCH', 'MISMATCH')
        )
        
        # EFT Recon
        eft_raw = pd.read_csv(DATA_DIR / 'eft_recon.csv') if IS_CLOUD else pd.read_excel(WORKBOOK_PATH, sheet_name='EFT Recon', header=1)
        eft_raw.columns = [str(c).strip().replace('\n', ' ') for c in eft_raw.columns]
        eft_cols = eft_raw.columns.tolist()
        if len(eft_cols) >= 19:
            eft_rename = {
                eft_cols[0]: 'EFT_Date', eft_cols[1]: 'Reference', 
                eft_cols[2]: 'Period_Start', eft_cols[3]: 'Period_End',
                eft_cols[4]: 'Num_Days', eft_cols[5]: 'Sum_Invoices',
                eft_cols[6]: 'Consignment', eft_cols[7]: 'Invoice_Variance',
                eft_cols[8]: 'Gross_CC', eft_cols[9]: 'CC_Fees',
                eft_cols[10]: 'Fuelman_Gross', eft_cols[11]: 'Fuelman_Fees',
                eft_cols[12]: 'Expected_Draft', eft_cols[13]: 'Actual_Draft',
                eft_cols[14]: 'Difference', eft_cols[15]: 'Direction',
                eft_cols[16]: 'Invoice_Match', eft_cols[17]: 'Settlement_Match',
                eft_cols[18]: 'Notes',
            }
            eft = eft_raw.rename(columns=eft_rename)
        else:
            eft = eft_raw
        eft = eft[eft.iloc[:, 0].notna()].copy()
        
        # Compute EFT derived values
        for col in ['Consignment', 'Gross_CC', 'CC_Fees', 'Fuelman_Gross', 'Fuelman_Fees', 'Actual_Draft']:
            if col in eft.columns:
                eft[col] = pd.to_numeric(eft[col], errors='coerce')
        
        if 'Consignment' in eft.columns and 'Gross_CC' in eft.columns:
            eft['Expected_Draft'] = (eft['Gross_CC'] - eft['CC_Fees'].fillna(0)) + (eft['Fuelman_Gross'].fillna(0) - eft['Fuelman_Fees'].fillna(0)) - eft['Consignment']
            eft['Difference'] = eft['Actual_Draft'] - eft['Expected_Draft']
            eft['Settlement_Match'] = np.where(
                eft['Actual_Draft'].isna(), '',
                np.where(abs(eft['Difference']) <= 0.01, 'MATCH', 'MISMATCH')
            )
            eft['Direction'] = np.where(
                eft['Expected_Draft'].isna(), '',
                np.where(eft['Expected_Draft'] > 0, 'Supplier Pays You',
                np.where(eft['Expected_Draft'] < 0, 'You Pay Supplier', 'Zero'))
            )
        
        return dr, eft
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

dr, eft = load_data()

# Keep unfiltered copies for EFT coverage calculations
dr_all = dr.copy() if dr is not None else None
eft_all = eft.copy() if eft is not None else None

def metric_card(label, value, color="blue", alert=None, subtext=""):
    alert_class = f"alert-{alert}" if alert else ""
    return f"""
    <div class="metric-card {color} {alert_class}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="subtext">{subtext}</div>
    </div>
    """

dark_layout = dict(
    paper_bgcolor='#161B22', plot_bgcolor='#161B22',
    font=dict(color='#8B949E', size=11),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor='#21262D', linecolor='#30363D'),
    yaxis=dict(gridcolor='#21262D', linecolor='#30363D'),
)

# ════════════════════════════════════════════
# TITLE
# ════════════════════════════════════════════
st.markdown("""
<div class="title-bar">
    <h1>GAS POW WOW <span style="color: #484F58; font-weight: 400;">FUEL RECONCILIATION</span></h1>
    <div class="subtitle">Daily Reconciliation & Profitability Command Center</div>
</div>
""", unsafe_allow_html=True)

if dr is None:
    st.error("Could not load workbook.")
    st.stop()

# ════════════════════════════════════════════
# DATE FILTER
# ════════════════════════════════════════════
dr['Date'] = pd.to_datetime(dr['Date'])
min_date = dr['Date'].min().date()
max_date = dr['Date'].max().date()

filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
with filter_col1:
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
with filter_col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
with filter_col3:
    quick = st.radio("Quick Range", ["All", "This Week", "This Month", "Last 30 Days", "Last 7 Days", "Custom"], 
                     horizontal=True, index=0)
    if quick == "Last 7 Days":
        start_date = (pd.Timestamp(max_date) - pd.Timedelta(days=7)).date()
    elif quick == "Last 30 Days":
        start_date = (pd.Timestamp(max_date) - pd.Timedelta(days=30)).date()
    elif quick == "This Month":
        start_date = max_date.replace(day=1)
    elif quick == "This Week":
        start_date = (pd.Timestamp(max_date) - pd.Timedelta(days=max_date.weekday())).date()

# Apply filter
dr = dr[(dr['Date'].dt.date >= start_date) & (dr['Date'].dt.date <= end_date)]

if eft is not None:
    if 'EFT_Date' in eft.columns:
        eft['EFT_Date'] = pd.to_datetime(eft['EFT_Date'])
        eft = eft[(eft['EFT_Date'].dt.date >= start_date) & (eft['EFT_Date'].dt.date <= end_date)]

st.markdown(f"""
<div style="color: #484F58; font-size: 12px; margin-bottom: 16px;">
    Showing data from <span style="color: #58A6FF;">{start_date.strftime('%b %d, %Y')}</span> 
    to <span style="color: #58A6FF;">{end_date.strftime('%b %d, %Y')}</span> 
    ({len(dr)} days)
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# DAILY RECON HEALTH
# ════════════════════════════════════════════
st.markdown('<div class="section-header"> DAILY RECON HEALTH</div>', unsafe_allow_html=True)

days = len(dr)
sales_mm = int((dr['Sales_Match'] == 'MISMATCH').sum())
gallon_mm = int((dr['Gallon_Match'] == 'MISMATCH').sum())
eft_count = len(eft) if eft is not None else 0
eft_settle_mm = int((eft['Settlement_Match'] == 'MISMATCH').sum()) if eft is not None and 'Settlement_Match' in eft.columns else 0
net_eft_diff = eft['Difference'].sum() if eft is not None and 'Difference' in eft.columns else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(metric_card("Days Recorded", str(days), "blue", subtext="total entries"), unsafe_allow_html=True)
with c2:
    alert = "red" if sales_mm > 0 else "green"
    st.markdown(metric_card("Sales Mismatches", str(sales_mm), "red", alert=alert), unsafe_allow_html=True)
with c3:
    alert = "red" if gallon_mm > 0 else "green"
    st.markdown(metric_card("Gallon Mismatches", str(gallon_mm), "red", alert=alert), unsafe_allow_html=True)
with c4:
    st.markdown(metric_card("EFTs Processed", str(eft_count), "cyan", subtext="on EFT Recon"), unsafe_allow_html=True)
with c5:
    alert = "red" if eft_settle_mm > 0 else "green"
    st.markdown(metric_card("EFT Mismatches", str(eft_settle_mm), "red", alert=alert), unsafe_allow_html=True)
with c6:
    alert = "red" if abs(net_eft_diff) > 0.01 else "green"
    val = f"${net_eft_diff:,.2f}" if not pd.isna(net_eft_diff) else "$0.00"
    st.markdown(metric_card("Net EFT Diff", val, "orange", alert=alert), unsafe_allow_html=True)

# ════════════════════════════════════════════
# MONEY OWED ALERT
# ════════════════════════════════════════════

# Calculate EFT settlement discrepancies
eft_diff_val = 0
if eft is not None and 'Difference' in eft.columns:
    eft_diff_val = eft['Difference'].sum()

# Calculate unsettled days using settled_dates.json
# A day is settled if its date appears in the settled_dates map
# A day is unsettled if it has gas report data but is NOT in settled_dates
# Unsettled amount = Gas Report CC - Meter Fuel Sales for each unsettled day
import json as _json

SETTLED_DATES_PATH = str(DATA_DIR / 'settled_dates.json') if IS_CLOUD else os.path.join(
    os.environ.get("USERPROFILE", ""), ".openclaw", "workspace", "fuel_automation", "settled_dates.json"
)

@st.cache_data(ttl=30)
def load_settled_dates():
    try:
        with open(SETTLED_DATES_PATH, "r") as f:
            return _json.load(f)
    except Exception:
        return {}

settled_dates_map = load_settled_dates()

unsettled_total = 0
unsettled_days = 0
unsettled_detail = []

for _, row in dr.iterrows():
    has_gas_report = pd.notna(row.get('Meter_Sales')) and row['Meter_Sales'] > 0
    if has_gas_report:
        day_str = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        is_settled = day_str in settled_dates_map
        
        if not is_settled:
            cc = row['Gas_CC'] if pd.notna(row.get('Gas_CC')) else 0
            sales = row['Meter_Sales']
            owed = cc - sales
            unsettled_total += owed
            unsettled_days += 1
            unsettled_detail.append({'Date': pd.to_datetime(row['Date']).date(), 'CC': cc, 'Sales': sales, 'Owed': owed})

total_owed = eft_diff_val + unsettled_total

# Display
owed_col1, owed_col2, owed_col3 = st.columns(3)

with owed_col1:
    color = "#3FB950" if eft_diff_val > 0 else "#F85149" if eft_diff_val < 0 else "#8B949E"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #161B22 0%, #1a2e1a 100%); 
         border: 1px solid #30363D; border-radius: 12px; padding: 20px; text-align: center;">
        <div style="font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
            EFT Settlement Discrepancies
        </div>
        <div style="font-size: 36px; font-weight: 700; color: {color};">
            ${eft_diff_val:,.2f}
        </div>
        <div style="font-size: 11px; color: #484F58; margin-top: 4px;">
            {eft_settle_mm} mismatched out of {eft_count} EFTs
        </div>
    </div>
    """, unsafe_allow_html=True)

with owed_col2:
    unsettled_color = "#D29922" if unsettled_days > 0 else "#8B949E"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #161B22 0%, #2D2410 100%); 
         border: 1px solid #30363D; border-radius: 12px; padding: 20px; text-align: center;">
        <div style="font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
            Unsettled Invoices
        </div>
        <div style="font-size: 36px; font-weight: 700; color: {unsettled_color};">
            ${unsettled_total:,.2f}
        </div>
        <div style="font-size: 11px; color: #484F58; margin-top: 4px;">
            {unsettled_days} days with no EFT coverage
        </div>
    </div>
    """, unsafe_allow_html=True)

with owed_col3:
    total_color = "#3FB950" if total_owed > 0 else "#F85149"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0D2818 0%, #1a4d2e 100%); 
         border: 2px solid #3FB950; border-radius: 12px; padding: 20px; text-align: center;">
        <div style="font-size: 11px; color: #3FB950; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;">
             TOTAL OWED TO YOU
        </div>
        <div style="font-size: 42px; font-weight: 700; color: {total_color};">
            ${total_owed:,.2f}
        </div>
        <div style="font-size: 11px; color: #484F58; margin-top: 4px;">
            Settlement discrepancies + unsettled invoices
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════
# PROFITABILITY
# ════════════════════════════════════════════
st.markdown('<div class="section-header"> PROFITABILITY & PERFORMANCE</div>', unsafe_allow_html=True)

total_sales = dr['Invoice_Sales'].sum()
total_cost = dr['Fuel_Cost'].sum()
total_profit = dr['Fuel_Profit'].sum()
avg_margin = dr['Margin_Per_Gallon'].dropna().mean()
total_gallons = dr['Invoice_Gallons'].sum()
total_cc = dr['Gas_CC'].sum()

p1, p2, p3, p4, p5, p6 = st.columns(6)
with p1:
    st.markdown(metric_card("Total Sales", f"${total_sales:,.0f}", "blue"), unsafe_allow_html=True)
with p2:
    st.markdown(metric_card("Total Cost", f"${total_cost:,.0f}", "purple"), unsafe_allow_html=True)
with p3:
    st.markdown(metric_card("Total Profit", f"${total_profit:,.0f}", "green", alert="green"), unsafe_allow_html=True)
with p4:
    margin_str = f"${avg_margin:.3f}" if not pd.isna(avg_margin) else "N/A"
    alert = "amber" if (not pd.isna(avg_margin) and avg_margin < 0.03) else None
    st.markdown(metric_card("Avg Margin/Gal", margin_str, "green", alert=alert), unsafe_allow_html=True)
with p5:
    st.markdown(metric_card("Total Gallons", f"{total_gallons:,.0f}", "cyan"), unsafe_allow_html=True)
with p6:
    st.markdown(metric_card("Total Gas CC", f"${total_cc:,.0f}", "orange"), unsafe_allow_html=True)

# ════════════════════════════════════════════
# CHARTS
# ════════════════════════════════════════════
st.markdown('<div class="section-header"> TRENDS & GAUGES</div>', unsafe_allow_html=True)

# Top row: Profit trend (left), EFT over/under payment detail (right)
chart_left, chart_right = st.columns([1, 1])

with chart_left:
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=dr['Date'], y=dr['Fuel_Profit'],
        marker_color='#3FB950', marker_line_width=0, name='Fuel Profit',
    ))
    fig_bar.update_layout(**dark_layout, title=dict(text="Daily Fuel Profit", font=dict(color='#E6EDF3', size=14)),
                          height=320, showlegend=False, yaxis_tickprefix='$')
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

with chart_right:
    # EFT Discrepancy table — date, amount, running balance
    if eft is not None and 'Difference' in eft.columns:
        all_efts = eft[eft['Difference'].notna()][['EFT_Date', 'Difference']].copy()
        all_efts = all_efts.sort_values('EFT_Date')
        all_efts['Running_Balance'] = all_efts['Difference'].cumsum()
        # Only show mismatched ones but with running balance
        mismatched = all_efts[abs(all_efts['Difference']) > 0.01].copy()
        mismatched['EFT_Date'] = pd.to_datetime(mismatched['EFT_Date']).dt.strftime('%m/%d/%Y')
        mismatched['Difference'] = mismatched['Difference'].apply(lambda x: f'${x:,.2f}')
        mismatched['Running_Balance'] = mismatched['Running_Balance'].apply(lambda x: f'${x:,.2f}')
        mismatched = mismatched.rename(columns={
            'EFT_Date': 'Date', 'Difference': 'Shorted', 'Running_Balance': 'Running Total'
        })
        
        st.markdown("""
        <div style="background: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 16px;">
            <div style="font-size: 14px; font-weight: 600; color: #E6EDF3; margin-bottom: 4px;">
                 EFT Settlement Discrepancies
            </div>
            <div style="font-size: 11px; color: #8B949E;">Per-EFT shortage + cumulative running total</div>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(mismatched, use_container_width=True, height=280, hide_index=True)

# Second row: Gallons sold trend (left), Match gauges (right)
ch2_left, ch2_mid, ch2_right = st.columns([2, 1, 1])

with ch2_left:
    # Daily gallons sold
    gal_data = dr[dr['Invoice_Gallons'].notna()]
    fig_gal = go.Figure()
    fig_gal.add_trace(go.Bar(
        x=gal_data['Date'], y=gal_data['Invoice_Gallons'],
        marker_color='#58A6FF', marker_line_width=0, name='Gallons',
        hovertemplate='%{x}<br>Gallons: %{y:,.0f}<extra></extra>',
    ))
    fig_gal.update_layout(**dark_layout, 
        title=dict(text="Daily Gallons Sold", font=dict(color='#E6EDF3', size=14)),
        height=280, showlegend=False, yaxis_title="Gallons")
    st.plotly_chart(fig_gal, use_container_width=True, config={'displayModeBar': False})

with ch2_mid:
    # Sales match donut (smaller)
    s_match = int((dr['Sales_Match'] == 'MATCH').sum())
    s_mismatch = int((dr['Sales_Match'] == 'MISMATCH').sum())
    s_total = max(s_match + s_mismatch, 1)
    pct = s_match / s_total * 100
    
    fig_d1 = go.Figure(go.Pie(
        values=[s_match, s_mismatch], labels=['Match', 'Mismatch'],
        hole=0.7, marker=dict(colors=['#3FB950', '#F85149']), textinfo='none',
    ))
    d1_layout = {k: v for k, v in dark_layout.items() if k != 'margin'}
    fig_d1.update_layout(**d1_layout, title=dict(text="Sales Match", font=dict(color='#E6EDF3', size=12)),
                         height=220, showlegend=False, margin=dict(l=20, r=20, t=40, b=20),
                         annotations=[dict(text=f'{pct:.0f}%', x=0.5, y=0.5, font_size=22, 
                                          font_color='#3FB950' if pct > 90 else '#F85149', showarrow=False)])
    st.plotly_chart(fig_d1, use_container_width=True, config={'displayModeBar': False})

with ch2_right:
    # Gallon match donut (smaller)
    g_match = int((dr['Gallon_Match'] == 'MATCH').sum())
    g_mismatch = int((dr['Gallon_Match'] == 'MISMATCH').sum())
    g_total = max(g_match + g_mismatch, 1)
    gpct = g_match / g_total * 100
    
    fig_d2 = go.Figure(go.Pie(
        values=[g_match, g_mismatch], labels=['Match', 'Mismatch'],
        hole=0.7, marker=dict(colors=['#58A6FF', '#F85149']), textinfo='none',
    ))
    d2_layout = {k: v for k, v in dark_layout.items() if k != 'margin'}
    fig_d2.update_layout(**d2_layout, title=dict(text="Gallon Match", font=dict(color='#E6EDF3', size=12)),
                         height=220, showlegend=False, margin=dict(l=20, r=20, t=40, b=20),
                         annotations=[dict(text=f'{gpct:.0f}%', x=0.5, y=0.5, font_size=22,
                                          font_color='#58A6FF' if gpct > 90 else '#F85149', showarrow=False)])
    st.plotly_chart(fig_d2, use_container_width=True, config={'displayModeBar': False})

# ════════════════════════════════════════════
# RECENT TRANSACTIONS
# ════════════════════════════════════════════
st.markdown('<div class="section-header"> RECENT DAILY RECONCILIATION</div>', unsafe_allow_html=True)

display_cols = ['Date', 'Meter_Sales', 'Invoice_Sales', 'Sales_Diff', 'Meter_Gallons', 
                'Invoice_Gallons', 'Gallon_Diff', 'Gas_CC', 'Fuel_Cost', 'Fuel_Profit',
                'Margin_Per_Gallon', 'Sales_Match', 'Gallon_Match']
available = [c for c in display_cols if c in dr.columns]
display_df = dr[available].copy()

# Format
fmt_map = {
    'Meter_Sales': '${:,.2f}', 'Invoice_Sales': '${:,.2f}', 'Sales_Diff': '${:,.2f}',
    'Gas_CC': '${:,.2f}', 'Fuel_Cost': '${:,.2f}', 'Fuel_Profit': '${:,.2f}',
    'Margin_Per_Gallon': '${:,.3f}', 'Meter_Gallons': '{:,.1f}', 'Invoice_Gallons': '{:,.0f}',
    'Gallon_Diff': '{:,.3f}',
}
for col, fmt in fmt_map.items():
    if col in display_df:
        display_df[col] = display_df[col].apply(lambda x: fmt.format(x) if pd.notna(x) else '')

rename_display = {
    'Meter_Sales': 'Meter $', 'Invoice_Sales': 'Invoice $', 'Sales_Diff': 'Sales Diff',
    'Meter_Gallons': 'Meter Gal', 'Invoice_Gallons': 'Inv Gal', 'Gallon_Diff': 'Gal Diff',
    'Gas_CC': 'Gas CC', 'Fuel_Cost': 'Cost', 'Fuel_Profit': 'Profit',
    'Margin_Per_Gallon': 'Margin', 'Sales_Match': 'Sales', 'Gallon_Match': 'Gallon',
}
display_df = display_df.rename(columns=rename_display)

st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)

# ════════════════════════════════════════════
# EFT MISMATCH DETAIL
# ════════════════════════════════════════════
if eft is not None and 'Difference' in eft.columns:
    mismatched_efts = eft[abs(eft['Difference']) > 0.01].copy()
    if len(mismatched_efts) > 0:
        st.markdown('<div class="section-header"> EFT SETTLEMENT MISMATCHES</div>', unsafe_allow_html=True)
        
        eft_display_cols = ['EFT_Date', 'Consignment', 'Gross_CC', 'CC_Fees', 'Fuelman_Gross',
                           'Expected_Draft', 'Actual_Draft', 'Difference', 'Direction']
        eft_available = [c for c in eft_display_cols if c in mismatched_efts.columns]
        eft_display = mismatched_efts[eft_available].copy()
        
        eft_fmt = {
            'Consignment': '${:,.2f}', 'Gross_CC': '${:,.2f}', 'CC_Fees': '${:,.2f}',
            'Fuelman_Gross': '${:,.2f}', 'Expected_Draft': '${:,.2f}', 
            'Actual_Draft': '${:,.2f}', 'Difference': '${:,.2f}',
        }
        for col, fmt in eft_fmt.items():
            if col in eft_display:
                eft_display[col] = eft_display[col].apply(lambda x: fmt.format(x) if pd.notna(x) else '')
        
        eft_rename = {
            'EFT_Date': 'Date', 'Consignment': 'Settlement', 'Gross_CC': 'Gross CC',
            'CC_Fees': 'CC Fees', 'Fuelman_Gross': 'Fuelman', 'Expected_Draft': 'Expected',
            'Actual_Draft': 'Actual', 'Difference': 'Diff (Owed)',
        }
        eft_display = eft_display.rename(columns=eft_rename)
        
        st.dataframe(eft_display, use_container_width=True, height=400, hide_index=True)

# ════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════
st.markdown("""
<div style="text-align: center; padding: 24px 0; color: #484F58; font-size: 12px; 
     border-top: 1px solid #21262D; margin-top: 32px;">
    POW WOW LLC  ·  Prince Oil Company  ·  Fuel Reconciliation Command Center
</div>
""", unsafe_allow_html=True)
