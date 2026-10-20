# 📈 Subscription Finance & At-Risk Revenue Optimization Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://subscription-finance-engine-nbj6dclzjeg6kvxa3zng9e.streamlit.app/)

> **🚀 Live Interactive Application:** [Click here to view the Live Dashboard](https://subscription-finance-engine-nbj6dclzjeg6kvxa3zng9e.streamlit.app/)

An end-to-end quantitative financial engineering and predictive risk scoring system built using the real-world IBM Telco Customer Churn dataset.

This enterprise pipeline bridges machine learning with corporate finance by calculating continuous churn risk probabilities and mapping them directly to dollar-weighted revenue exposure (\$ Expected Loss).

---

## 🛠️ Tech Stack & Architecture

- **Database & Data Pipeline:** SQLite, SQL (CTEs, Window Functions `DENSE_RANK() OVER`)
- **Data Analytics & Vectorization:** Python, Pandas, NumPy (Vectorized $LTV$, $ARR$, Risk Multipliers)
- **Predictive Machine Learning:** Scikit-Learn, Random Forest Classifier (`predict_proba`)
- **Executive Dashboard:** Streamlit, Plotly Express

---

## 📊 End-to-End Workflow

1. **SQL Database Ingestion (`telecom_finance.db`):** 
   - Loaded raw transactional data into SQLite.
   - Applied SQL CTEs to handle missing values (`COALESCE`, `NULLIF`, `TRIM`) and generated tenure cohort buckets.
2. **Financial Metric Engineering:** 
   - Vectorized computation of **Historical LTV** ($\text{MonthlyCharges} \times \text{Tenure}$) and **ARR**.
   - Applied dynamic risk multipliers ($1.5\times$) for vulnerable contract-internet segments (Month-to-Month + Fiber Optic).
3. **Predictive Risk ML Pipeline:**
   - Trained a `RandomForestClassifier` with One-Hot Encoding.
   - Extracted continuous churn probabilities ($0.0$ to $1.0$) and derived **Expected Revenue Loss** ($\text{Churn Risk} \times \text{Monthly Charges}$).
4. **Interactive Streamlit Executive Hub (`app.py`):**
   - Interactive Portfolio KPIs, Cohort Heatmaps, Individual Scatter Plots, and a Retention Action List with CSV export capabilities.

---

## 🚀 How to Run Locally

```bash
# 1. Clone the repository
git clone [https://github.com/Gauri-42/subscription-finance-engine.git](https://github.com/Gauri-42/subscription-finance-engine.git)
cd subscription-finance-engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Streamlit Dashboard
streamlit run app.py