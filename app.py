import streamlit as st
import pandas as pd
from thefuzz import process
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RFM Dashboard",
    page_icon="☕",
    layout="wide"
)

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("☕ Customer RFM Dashboard")
st.markdown("Upload your Wix exports to automatically segment customers and generate Mailchimp-ready lists.")

# ── Sidebar instructions ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("How to use")
    st.markdown("""
    **Step 1** — Export from Wix:
    - *Orders*: Store → Orders → Export  
      *(include Date created, Contact email, Recipient name)*
    - *Customers*: People → Top Paying Customers → Export  
      *(include Customer name, Orders, Total sales)*

    **Step 2** - Review segments and download your Mailchimp list
    """)
    st.divider()
    st.markdown("Built by BNH Research & Marketing Intern, Summer 2026")

# ── File upload ───────────────────────────────────────────────────────────────
st.subheader("Step 1: Upload your two Wix exports")
st.caption("Both files are required. Make sure both cover the **same date range**.")

col_info1, col_info2 = st.columns(2)
with col_info1:
    st.info("""
    **Orders CSV**  
    Export from: Store → Orders → Export  
    Required columns:
    - Date created
    - Recipient name
    - Contact email
    """)
with col_info2:
    st.info("""
    **Customers CSV**  
    Export from: People → Top Paying Customers → Export  
    Required columns:
    - Customer name
    - Orders
    - Total sales
    """)


col1, col2 = st.columns(2)

with col1:
    orders_file = st.file_uploader("📦 Upload Orders CSV", type="csv")

with col2:
    customers_file = st.file_uploader("👥 Upload Customers CSV", type="csv")

# Warning if only one file uploaded
if orders_file and not customers_file:
    st.warning("⚠️ Orders file uploaded — please also upload the Customers CSV to continue.")
elif customers_file and not orders_file:
    st.warning("⚠️ Customers file uploaded — please also upload the Orders CSV to continue.")

# ── Helper functions ──────────────────────────────────────────────────────────

def clean_email(email_series):
    """Strip markdown formatting from emails like [email](mailto:email)"""
    cleaned = email_series.str.extract(r'\[(.+?)\]')[0]
    # If extract returns NaN (no markdown), use original
    return cleaned.fillna(email_series)

def clean_currency(series):
    """Remove $ and , from currency strings and convert to float"""
    return series.str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

def split_name(full_name):
    """Split full name into first and last name"""
    parts = str(full_name).strip().split()
    if len(parts) == 0:
        return '', ''
    elif len(parts) == 1:
        return parts[0], ''
    else:
        return parts[0], ' '.join(parts[1:])

def assign_segment(row):
    """Assign RFM segment label based on R, F, M scores"""
    r = int(row['R_score'])
    f = int(row['F_score'])
    m = int(row['M_score'])

    if r == 3 and f == 3 and m == 3:
        return 'Champion'
    elif r == 3 and f >= 2 and m >= 2:
        return 'Loyal'
    elif r == 3 and f == 1 and m == 1:
        return 'New Customer'
    elif r == 2 and f >= 2:
        return 'Promising'
    elif r == 1 and f >= 2 and m >= 2:
        return 'At Risk'
    elif r == 1 and f >= 2 and m == 1:
        return 'Needs Attention'
    else:
        return 'Lost'

SEGMENT_COLORS = {
    'Champion':        '#2ecc71',
    'Loyal':           '#27ae60',
    'Promising':       '#3498db',
    'New Customer':    '#1abc9c',
    'Needs Attention': '#f39c12',
    'At Risk':         '#e74c3c',
    'Lost':            '#95a5a6',
}

SEGMENT_ACTIONS = {
    'Champion':        'VIP treatment; early access to new shipments; referral ask',
    'Loyal':           'Subscription upgrade offer; thank-you email',
    'Promising':       'Follow-up email; introduce subscription; feature Medium Roast',
    'New Customer':    '"How did you like your coffee?" email + subscribe offer',
    'Needs Attention': 'Low-cost automated email; low priority',
    'At Risk':         'Urgent personalized re-engagement; strong incentive offer',
    'Lost':            'Single automated re-engagement; minimal effort',
}

ORG_KEYWORDS = [
    'co-op', 'coop', 'inc', 'llc', 'ltd', 'church', 'society',
    'conservancy', 'foundation', 'global', 'panaderia', 'escuelita',
    'harvest', 'whole foods', 'building new hope', 'ascender',
    'ten thousand', 'frankferd', 'villages', 'links'
]

def is_org(name):
    """Heuristic to detect organization accounts"""
    name_lower = str(name).lower()
    return any(kw in name_lower for kw in ORG_KEYWORDS)

# ── Main analysis ─────────────────────────────────────────────────────────────

if orders_file and customers_file:
    with st.spinner("Analyzing customer data..."):

        # Load files
        orders = pd.read_csv(orders_file)
        customers = pd.read_csv(customers_file)

        # ── Clean orders ──
        # Detect date, email, name columns flexibly
        date_col   = [c for c in orders.columns if 'date' in c.lower()][0]
        email_col  = [c for c in orders.columns if 'email' in c.lower()][0]
        name_col   = [c for c in orders.columns if 'name' in c.lower() or 'recipient' in c.lower()][0]

        orders[date_col]  = pd.to_datetime(orders[date_col])
        orders[email_col] = clean_email(orders[email_col])

        reference_date = orders[date_col].max()

        # Get last purchase date + email per recipient name
        last_purchase = orders.groupby(name_col).agg(
            Last_purchase=(date_col, 'max'),
            Email=(email_col, 'first')
        ).reset_index()
        last_purchase.columns = ['Customer name', 'Last_purchase', 'Email']
        last_purchase['Recency'] = (reference_date - last_purchase['Last_purchase']).dt.days

        # Build name→email and name→recency dicts
        recency_lookup = last_purchase.set_index('Customer name')['Recency'].to_dict()
        email_lookup   = last_purchase.set_index('Customer name')['Email'].to_dict()

        # ── Clean customers ──
        cust_name_col  = [c for c in customers.columns if 'name' in c.lower()][0]
        cust_order_col = [c for c in customers.columns if 'order' in c.lower()][0]
        cust_sales_col = [c for c in customers.columns if 'sales' in c.lower() or 'total' in c.lower()][0]

        customers = customers.rename(columns={
            cust_name_col:  'Customer name',
            cust_order_col: 'Frequency',
            cust_sales_col: 'Monetary'
        })
        customers['Monetary'] = clean_currency(customers['Monetary'])

        # Remove org accounts
        customers['is_org'] = customers['Customer name'].apply(is_org)
        orgs_removed = customers['is_org'].sum()
        customers = customers[~customers['is_org']].copy()

        # ── Merge recency ──
        customers['Recency'] = customers['Customer name'].map(recency_lookup)

        # Fuzzy match for unmatched names
        order_names = last_purchase['Customer name'].tolist()
        unmatched = customers[customers['Recency'].isnull()]['Customer name'].tolist()

        fuzzy_fixes = {}
        for name in unmatched:
            match = process.extractOne(name, order_names)
            if match and match[1] >= 80:
                fuzzy_fixes[name] = match[0]

        for cust_name, order_name in fuzzy_fixes.items():
            if order_name in recency_lookup:
                customers.loc[customers['Customer name'] == cust_name, 'Recency'] = recency_lookup[order_name]
            if order_name in email_lookup:
                customers.loc[customers['Customer name'] == cust_name, 'Email'] = email_lookup[order_name]

        # Drop still-unmatched
        unmatched_final = customers[customers['Recency'].isnull()]['Customer name'].tolist()
        rfm = customers.dropna(subset=['Recency']).copy()

        # ── Add email ──
        rfm['Email'] = rfm['Customer name'].map(email_lookup)
        # Fill from fuzzy matches
        for cust_name, order_name in fuzzy_fixes.items():
            if order_name in email_lookup:
                rfm.loc[rfm['Customer name'] == cust_name, 'Email'] = email_lookup[order_name]

        # ── RFM Scoring ──
        rfm['R_score'] = pd.qcut(rfm['Recency'], q=3, labels=[3, 2, 1])
        rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=3, labels=[1, 2, 3])
        rfm['M_score'] = pd.qcut(rfm['Monetary'].rank(method='first'),  q=3, labels=[1, 2, 3])
        rfm['Segment'] = rfm.apply(assign_segment, axis=1)

        # ── Split name ──
        rfm[['First name', 'Last name']] = rfm['Customer name'].apply(
            lambda x: pd.Series(split_name(x))
        )

    # ── Dashboard ─────────────────────────────────────────────────────────────

    st.success(f"Analysis complete — {len(rfm)} customers segmented")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total customers", len(rfm))
    col2.metric("Orgs removed", int(orgs_removed))
    col3.metric("Fuzzy matched", len(fuzzy_fixes))
    col4.metric("Unmatched (dropped)", len(unmatched_final))

    st.divider()

    # Segment overview
    st.subheader("Segment overview")

    seg_summary = rfm.groupby('Segment').agg(
        Customers=('Customer name', 'count'),
        Total_revenue=('Monetary', 'sum'),
        Avg_revenue=('Monetary', 'mean'),
        Avg_recency=('Recency', 'mean'),
    ).round(1).reset_index().sort_values('Total_revenue', ascending=False)
    seg_summary['Recommended action'] = seg_summary['Segment'].map(SEGMENT_ACTIONS)
    seg_summary['Total_revenue'] = seg_summary['Total_revenue'].apply(lambda x: f'${x:,.0f}')
    seg_summary['Avg_revenue']   = seg_summary['Avg_revenue'].apply(lambda x: f'${x:,.0f}')
    seg_summary.columns = ['Segment', 'Customers', 'Total Revenue', 'Avg Revenue', 'Avg Days Since Purchase', 'Recommended Action']

    st.dataframe(seg_summary, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Segment visualization")

    import matplotlib.pyplot as plt
    import numpy as np

    seg_data = rfm.groupby('Segment').agg(
        Customers=('Customer name', 'count'),
        Total_revenue=('Monetary', 'sum')
    ).reset_index().sort_values('Total_revenue', ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor('#f8f9fa')

    bar_colors = [SEGMENT_COLORS.get(s, '#95a5a6') for s in seg_data['Segment']]

    # Left — customer count
    axes[0].barh(seg_data['Segment'], seg_data['Customers'], color=bar_colors, alpha=0.85)
    axes[0].set_title('Customers per Segment', fontweight='bold')
    axes[0].set_xlabel('Number of Customers')
    for i, val in enumerate(seg_data['Customers']):
        axes[0].text(val + 0.3, i, str(val), va='center', fontweight='bold')
    axes[0].spines['top'].set_visible(False)
    axes[0].spines['right'].set_visible(False)

    # Right — revenue
    axes[1].barh(seg_data['Segment'], seg_data['Total_revenue'], color=bar_colors, alpha=0.85)
    axes[1].set_title('Total Revenue per Segment ($)', fontweight='bold')
    axes[1].set_xlabel('Total Revenue ($)')
    axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    for i, val in enumerate(seg_data['Total_revenue']):
        axes[1].text(val + 50, i, f'${val:,.0f}', va='center', fontweight='bold', fontsize=9)
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['right'].set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)

    st.divider()

    # Segment filter + download
    st.subheader("Export Mailchimp list by segment")

    selected_segment = st.selectbox(
        "Select a segment to export:",
        options=['All segments'] + sorted(rfm['Segment'].unique().tolist())
    )

    if selected_segment == 'All segments':
        export_df = rfm.copy()
    else:
        export_df = rfm[rfm['Segment'] == selected_segment].copy()

    # Build Mailchimp-ready export
    mailchimp_df = export_df[[
        'First name', 'Last name', 'Customer name', 'Email',
        'Segment', 'Recency', 'Frequency', 'Monetary',
        'R_score', 'F_score', 'M_score'
    ]].copy()
    mailchimp_df['R_score'] = mailchimp_df['R_score'].astype(int)
    mailchimp_df['F_score'] = mailchimp_df['F_score'].astype(int)
    mailchimp_df['M_score'] = mailchimp_df['M_score'].astype(int)
    mailchimp_df = mailchimp_df.sort_values('Monetary', ascending=False)

    st.write(f"**{len(mailchimp_df)} customers** in this export:")
    st.dataframe(mailchimp_df, use_container_width=True, hide_index=True)

    # Download button
    csv_buffer = io.StringIO()
    mailchimp_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label=f"⬇️ Download {selected_segment} list as CSV",
        data=csv_buffer.getvalue(),
        file_name=f"BNH_RFM_{selected_segment.replace(' ', '_')}.csv",
        mime="text/csv"
    )

    st.divider()
    st.caption(f"Reference date: {reference_date.strftime('%b %d, %Y')} | Analysis covers Jan 2024 – present")

else:
    st.info("👆 Upload both CSV files above to get started.")

    st.divider()
    
    st.subheader("What is RFM?")
    st.markdown("""
    **RFM** is a standard marketing analytics technique that scores each customer on three dimensions:
    
    | Dimension | What it measures | Better score means... |
    |---|---|---|
    | **R**ecency | Days since last purchase | Bought more recently |
    | **F**requency | Total number of orders | Orders more often |
    | **M**onetary | Total amount spent | Spends more |
    
    Each customer gets a score of 1–3 on each dimension and is assigned to one of seven segments:
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - 🟢 **Champion** — recent, frequent, high spend
        - 🟢 **Loyal** — regular repeat buyers  
        - 🔵 **Promising** — recent but not yet frequent
        - 🩵 **New Customer** — bought recently for the first time
        """)
    with col2:
        st.markdown("""
        - 🟠 **Needs Attention** — lapsed with low spend
        - 🔴 **At Risk** — valuable but haven't bought recently
        - ⚪ **Lost** — one-time or very lapsed buyers
        """)
    
    st.divider()
    
    st.markdown("""
    ### What this dashboard does
    - Automatically cleans and merges your Wix exports
    - Scores each customer on **Recency**, **Frequency**, and **Monetary** value
    - Assigns each customer to a segment: Champion, At Risk, Promising, Loyal, New Customer, Needs Attention, or Lost
    - Splits full names into First / Last name for Mailchimp
    - Exports a ready-to-upload CSV filtered by any segment
    """)
