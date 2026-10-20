import re
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. PAGE CONFIG & THEME

st.set_page_config(
    page_title="Subscription Revenue Risk Engine",
    page_icon="📈",
    layout="wide",
)


# 2. HELPER FUNCTIONS & CONSTANTS

RISK_BINS = [0, 0.30, 0.60, 0.80, 1.0001]
RISK_LABELS = ["Low", "Medium", "High", "Critical"]
RISK_COLORS = {
    "Low": "#2E7D32",      
    "Medium": "#F57F17",   
    "High": "#E65100",    
    "Critical": "#C62828"  
}
CONTRACT_ORDER = ["Month-to-month", "One year", "Two year"]


def money(x: float) -> str:
    """Format compact dollar amounts."""
    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"${x / 1_000:,.1f}K"
    return f"${x:,.0f}"


def cohort_sort_key(label) -> int:
    m = re.search(r"\d+", str(label))
    return int(m.group()) if m else 10**6


def suggest_action(row, median_charge: float) -> str:
    if row["Risk_Tier"] == "Critical" and row["MonthlyCharges"] >= median_charge:
        return "📞 Executive Outreach & Custom Discount"
    if row["Contract"] == "Month-to-month":
        return "🏷️ Offer Discounted 1-Year Contract"
    if row["Risk_Tier"] in ("High", "Critical"):
        return "✉️ Targeted Loyalty Perk"
    return "👀 Monitor"


# 3. DATA LOADING & PREPROCESSING

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("data/df_master_final_risk.csv")
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
    df["Risk_Tier"] = pd.cut(
        df["Churn_Probability"], bins=RISK_BINS, labels=RISK_LABELS, right=False
    ).astype(str)
    return df


df = load_data()

contract_options = [c for c in CONTRACT_ORDER if c in df["Contract"].unique()] + [
    c for c in df["Contract"].unique() if c not in CONTRACT_ORDER
]
cohort_options = sorted(df["Tenure_Cohort"].dropna().unique(), key=cohort_sort_key)


# 4. SIDEBAR CONTROLS

st.sidebar.title("🎛️ Dashboard Controls")

sel_contracts = st.sidebar.multiselect(
    "Contract Types",
    contract_options,
    default=contract_options,
    help="Filter data by contract type."
)
sel_cohorts = st.sidebar.multiselect(
    "Customer Tenure Cohorts",
    cohort_options,
    default=cohort_options,
    help="Filter data by tenure cohort."
)

st.sidebar.markdown("---")
risk_threshold = st.sidebar.slider(
    "Churn Risk Threshold",
    min_value=0.10,
    max_value=1.00,
    value=0.60,
    step=0.05,
    help="Flag active accounts at or above this predicted risk level."
)

# Apply Filters
dff = df[df["Contract"].isin(sel_contracts) & df["Tenure_Cohort"].isin(sel_cohorts)]

if dff.empty:
    st.warning("No customers match the current sidebar selections.")
    st.stop()

active = dff[dff["Churn"] == "No"]
churned = dff[dff["Churn"] == "Yes"]

if active.empty:
    st.warning("No active customers match the selected criteria.")
    st.stop()

flagged = active[active["Churn_Probability"] >= risk_threshold].copy()
median_charge = active["MonthlyCharges"].median()
flagged["Suggested_Action"] = flagged.apply(suggest_action, axis=1, median_charge=median_charge)
flagged = flagged.sort_values("Expected_Revenue_Loss", ascending=False)
flagged.insert(0, "Priority", np.arange(1, len(flagged) + 1))


# 5. HEADER & ONBOARDING GUIDE

st.title("📈 Subscription Revenue Risk Dashboard")
st.caption("Quantifying customer churn probability and dynamic revenue exposure across recurring accounts.")

with st.expander("ℹ️ How to use this dashboard", expanded=False):
    st.markdown(
        """
        - **📊 Portfolio Overview:** High-level financials and historical retention trends.
        - **🔍 Risk Exposure:** Interactive segmentation and probability distribution maps.
        - **🛡️ Retention Action List:** Priority-ranked accounts exceeding your risk threshold with exportable workflows.
        """
    )

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Portfolio Overview", "🔍 Risk Exposure", "🛡️ Retention Action List", "📖 Glossary & Rules"]
)


# TAB 1: PORTFOLIO OVERVIEW

with tab1:
    st.subheader("Core Executive Metrics")
    
    total_arr = active["ARR"].sum()
    exp_loss_total = active["Expected_Revenue_Loss"].sum()
    n_active = len(active)
    n_flagged = len(flagged)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Portfolio ARR", money(total_arr))
    m2.metric("Active Customer Count", f"{n_active:,}")
    m3.metric("Flagged High-Risk Accounts", f"{n_flagged:,}", delta=f"{n_flagged / n_active:.1%} of Portfolio", delta_color="off")
    m4.metric("Total Expected Revenue Loss", money(exp_loss_total))

    st.markdown("---")

    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("##### Historical Churn Rate by Contract")
        by_contract = (
            dff.groupby("Contract")["Churn"].apply(lambda x: (x == "Yes").mean() * 100).reset_index(name="Churn_Rate")
        )
        fig_c = px.bar(
            by_contract,
            x="Contract",
            y="Churn_Rate",
            text=by_contract["Churn_Rate"].map("{:.1f}%".format),
            category_orders={"Contract": contract_options},
            color_discrete_sequence=["#4F46E5"]
        )
        fig_c.update_traces(textposition="outside")
        fig_c.update_layout(yaxis_title="% Cancelled", xaxis_title="", height=320)
        st.plotly_chart(fig_c, use_container_width=True)

    with col_right:
        st.markdown("##### Historical Churn Rate by Tenure")
        by_tenure = (
            dff.groupby("Tenure_Cohort")["Churn"].apply(lambda x: (x == "Yes").mean() * 100).reset_index(name="Churn_Rate")
        )
        fig_t = px.bar(
            by_tenure,
            x="Tenure_Cohort",
            y="Churn_Rate",
            text=by_tenure["Churn_Rate"].map("{:.1f}%".format),
            category_orders={"Tenure_Cohort": cohort_options},
            color_discrete_sequence=["#0D9488"]
        )
        fig_t.update_traces(textposition="outside")
        fig_t.update_layout(yaxis_title="% Cancelled", xaxis_title="", height=320)
        st.plotly_chart(fig_t, use_container_width=True)

    st.markdown("---")
    st.markdown("##### Churn Heatmap Across Cohorts & Contracts")
    
    seg_hist = (
        dff.groupby(["Contract", "Tenure_Cohort"])
        .agg(Churn_Rate=("Churn", lambda x: (x == "Yes").mean() * 100))
        .reset_index()
    )
    heatmap_data = seg_hist.pivot(index="Tenure_Cohort", columns="Contract", values="Churn_Rate")
    heatmap_data = heatmap_data.reindex(
        index=[c for c in cohort_options if c in heatmap_data.index],
        columns=[c for c in contract_options if c in heatmap_data.columns]
    )
    
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Contract Type", y="Tenure Cohort", color="Churn Rate (%)"),
        color_continuous_scale="Reds",
        text_auto=".1f",
        aspect="auto"
    )
    fig_heatmap.update_layout(height=350)
    st.plotly_chart(fig_heatmap, use_container_width=True)


# TAB 2: RISK EXPOSURE

with tab2:
    st.subheader("Active Portfolio Risk Segmentation")
    
    tier_summary = (
        active.groupby("Risk_Tier")
        .agg(Customers=("customerID", "count"), Expected_Loss=("Expected_Revenue_Loss", "sum"))
        .reindex(RISK_LABELS)
        .fillna(0)
        .reset_index()
    )
    
    l, r = st.columns(2)
    
    with l:
        fig_n = px.bar(
            tier_summary,
            x="Risk_Tier",
            y="Customers",
            color="Risk_Tier",
            color_discrete_map=RISK_COLORS,
            text="Customers",
            title="Customer Count by Risk Tier"
        )
        fig_n.update_traces(textposition="outside")
        fig_n.update_layout(showlegend=False, yaxis_title="Customer Count", height=320)
        st.plotly_chart(fig_n, use_container_width=True)

    with r:
        fig_m = px.bar(
            tier_summary,
            x="Risk_Tier",
            y="Expected_Loss",
            color="Risk_Tier",
            color_discrete_map=RISK_COLORS,
            text=tier_summary["Expected_Loss"].map(money),
            title="Expected Revenue Loss by Risk Tier ($)"
        )
        fig_m.update_traces(textposition="outside")
        fig_m.update_layout(showlegend=False, yaxis_title="Expected Loss ($)", height=320)
        st.plotly_chart(fig_m, use_container_width=True)

    st.markdown("---")
    st.subheader("Individual Risk Map")
    st.caption("Each point represents an active customer. Customers above the dashed red line exceed your selected risk threshold.")
    
    fig_scatter = px.scatter(
        active,
        x="MonthlyCharges",
        y="Churn_Probability",
        color="Risk_Tier",
        color_discrete_map=RISK_COLORS,
        category_orders={"Risk_Tier": RISK_LABELS},
        hover_data=["customerID", "Contract", "Tenure_Cohort", "Expected_Revenue_Loss"],
        labels={
            "MonthlyCharges": "Monthly Charges ($)",
            "Churn_Probability": "Predicted Churn Risk (0.0 to 1.0)",
            "Risk_Tier": "Risk Tier"
        },
        opacity=0.75
    )
    fig_scatter.add_hline(
        y=risk_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Threshold: {risk_threshold:.0%}",
        annotation_position="bottom right"
    )
    fig_scatter.update_layout(height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)


# TAB 3: RETENTION ACTION LIST

with tab3:
    st.subheader("Priority Retention Action List")
    
    if flagged.empty:
        st.success("🎉 No active accounts currently exceed the selected risk threshold!")
    else:
        
        st.markdown("##### 💡 Revenue Recovery Simulator")
        sim_col1, sim_col2 = st.columns([1, 2])
        
        with sim_col1:
            save_rate = st.slider(
                "Assumed Retention Success Rate",
                min_value=5,
                max_value=100,
                value=30,
                step=5,
                format="%d%%"
            )
        
        recovered_loss = flagged["Expected_Revenue_Loss"].sum() * (save_rate / 100)
        
        with sim_col2:
            s1, s2 = st.columns(2)
            s1.metric("Flagged Revenue at Risk", money(flagged["Expected_Revenue_Loss"].sum()))
            s2.metric(f"Protected Revenue (@ {save_rate}%)", money(recovered_loss))

        st.markdown("---")
        
        
        table = flagged[
            [
                "Priority",
                "customerID",
                "Contract",
                "Tenure_Cohort",
                "MonthlyCharges",
                "Risk_Tier",
                "Churn_Probability",
                "Expected_Revenue_Loss",
                "Suggested_Action",
            ]
        ].copy()
        
        table["Churn_Probability"] = table["Churn_Probability"] * 100

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Priority": st.column_config.NumberColumn("Rank", width="small"),
                "customerID": "Customer ID",
                "Contract": "Contract",
                "Tenure_Cohort": "Tenure Cohort",
                "MonthlyCharges": st.column_config.NumberColumn("Monthly Bill", format="$%.2f"),
                "Risk_Tier": "Risk Tier",
                "Churn_Probability": st.column_config.ProgressColumn(
                    "Churn Probability", min_value=0, max_value=100, format="%.0f%%"
                ),
                "Expected_Revenue_Loss": st.column_config.NumberColumn("Expected Loss", format="$%.2f"),
                "Suggested_Action": "Actionable Next Step",
            },
        )

        st.download_button(
            label="📥 Export Action List as CSV",
            data=flagged.to_csv(index=False).encode("utf-8"),
            file_name=f"high_risk_accounts_threshold_{int(risk_threshold * 100)}.csv",
            mime="text/csv"
        )


# TAB 4: GLOSSARY & RULES

with tab4:
    st.subheader("Metric Definitions & Calculation Rules")
    st.markdown(
        r"""
        | Metric / Concept | Description |
        |---|---|
        | **Churn Probability** | Machine learning prediction ($0.0$ to $1.0$) estimating account cancellation likelihood. |
        | **Expected Revenue Loss** | Calculated as $\text{Monthly Charges} \times \text{Churn Probability}$. |
        | **Annual Recurring Revenue (ARR)** | Total annualized value of active subscriptions ($\text{Monthly Charges} \times 12$). |
        | **Customer Lifetime Value (LTV)** | Total cumulative historical revenue generated ($\text{Monthly Charges} \times \text{Tenure}$). |
        | **Risk Tiers** | Categorized into Low ($<30\%$), Medium ($30-60\%$), High ($60-80\%$), and Critical ($>80\%$). |
        """
    )
    
    st.markdown("##### 📋 Next-Step Rule Playbook Logic")
    st.markdown(
        f"""
        1. **Critical Risk & Monthly Charges &ge; ${median_charge:,.2f}:** Priority Executive Outreach.
        2. **Month-to-Month Contract:** Offer Discounted 1-Year Fixed Contract.
        3. **High / Critical Risk (Longer Contracts):** Direct Targeted Loyalty Offer.
        4. **All Other Accounts:** Routine Automated Monitoring.
        """
    )