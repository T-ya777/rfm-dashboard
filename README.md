# ☕ RFM Customer Segmentation Dashboard for Wix Stores

![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-ff4b4b?logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

An interactive web dashboard that turns your Wix store exports into actionable customer segments — no coding required. Upload two CSV files and get a Mailchimp-ready customer list in seconds.

> ⭐ **If this tool is useful to you, please consider giving it a star on GitHub!** It helps others discover the project and takes just one click.

---

## 👤 For users (no installation needed)

👉 **[Open the dashboard](https://rfm-dashboard-for-wix.streamlit.app/)** 

### What you need

**1. Orders CSV** — export from Wix:
- Go to **Store → Orders**
- Click **Export**
- Make sure these columns are included:
  - `Date created`
  - `Recipient name`
  - `Contact email`

**2. Customers CSV** — export from Wix:
- Go to **People → Top Paying Customers**
- Click **Customize columns** and make sure these are selected:
  - `Customer name`
  - `Orders`
  - `Total sales`
- Click **Export**

> ⚠️ Both files should cover the **same date range** for accurate results.

### How to use

1. Open the dashboard link above
2. Upload both CSV files
3. Review your customer segments
4. Select a segment and download your Mailchimp-ready list

---

## 📊 What is RFM?

RFM is a standard marketing analytics technique that scores each customer on three dimensions:

| Dimension | What it measures |
|---|---|
| **R**ecency | How many days since their last purchase — lower is better |
| **F**requency | How many total orders they have placed — higher is better |
| **M**onetary | How much they have spent in total — higher is better |

Each customer gets a score of 1–3 on each dimension, then is assigned to one of seven segments:

| Segment | Who they are | Suggested action |
|---|---|---|
| 🟢 Champion | Recent, frequent, high spend | VIP treatment; early access; referral ask |
| 🟢 Loyal | Regular repeat buyers | Subscription upgrade; thank-you email |
| 🔵 Promising | Recent but not yet frequent | Follow-up email; product introduction |
| 🩵 New Customer | Bought recently for the first time | "How did you like it?" + subscribe offer |
| 🟠 Needs Attention | Lapsed with low spend | Low-cost automated email |
| 🔴 At Risk | Valuable but haven't bought recently | Urgent personalized re-engagement |
| ⚪ Lost | One-time or very lapsed buyers | Single re-engagement; minimal effort |

---

## 🛠️ For developers

### Tech stack

- [Streamlit](https://streamlit.io) — web app framework
- [pandas](https://pandas.pydata.org) — data processing
- [thefuzz](https://github.com/seatgeek/thefuzz) — fuzzy name matching
- [matplotlib](https://matplotlib.org) — charts

### Run locally

```bash
# Clone the repo
git clone https://github.com/yourusername/bnh-rfm-dashboard.git
cd bnh-rfm-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

### Deploy your own instance (free)

1. Fork this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **New app** → select your forked repo → set main file to `app.py`
5. Click **Deploy**

You'll get a public URL like `yourname-rfm.streamlit.app` that anyone can open in a browser — no installation needed on their end.

### Project structure

```
bnh-rfm-dashboard/
├── app.py              # Main Streamlit app (frontend + backend)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

### How the analysis works

1. **Load** — reads both CSV files and detects column names flexibly
2. **Clean** — strips Wix email markdown formatting, removes `$` and `,` from currency
3. **Filter** — removes organization and wholesale accounts using keyword detection
4. **Merge** — joins orders and customers files on customer name
5. **Fuzzy match** — automatically resolves name spelling inconsistencies between files (e.g. "Ed Dally" → "Edward Dally") using 80% similarity threshold
6. **Score** — assigns R, F, M scores 1–3 using quantile-based division
7. **Segment** — maps score combinations to seven named segments
8. **Export** — splits full names into first/last, attaches email, outputs Mailchimp-ready CSV

### Notes and limitations

- This dashboard is designed and tested for **Wix exports specifically**. Other platforms (Shopify, WooCommerce, etc.) use different column names and may require code modifications (or modify the file to match the columns name and content).
- Organization and wholesale accounts are excluded from segmentation using keyword matching. The keyword list may need to be updated for different businesses.
- Customers whose names cannot be matched between the two files (after fuzzy matching) are excluded and counted in the dashboard summary.
- With small customer bases (<200 customers), RFM quantile scores should be treated as directional rather than statistically robust.

---

## 🙌 Contributing

Found a bug or have a suggestion? Feel free to open an issue or submit a pull request. All contributions welcome.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 👋 Built by

Research & Marketing Intern at building new hope, Summer 2026

*Built as part of a data analytics internship project analyzing coffee sales data for a nonprofit organization. The RFM segmentation logic, fuzzy matching pipeline, and Streamlit dashboard were designed and implemented from scratch using Python and pandas.*

> ⭐ **Found this useful? A GitHub star goes a long way — thank you!**
