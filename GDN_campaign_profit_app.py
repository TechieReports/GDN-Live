import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Campaign Revenue vs Spend Analyzer", layout="centered")
st.title("📊 Campaign Revenue vs Spend Analyzer 💰")

# Upload section
revenue_file = st.file_uploader("Upload Revenue CSV", type="csv")
spend_file = st.file_uploader("Upload Spend Excel", type=["xlsx"])

if revenue_file and spend_file:
    try:
        # --- Load and aggregate revenue ---
        revenue_df = pd.read_csv(revenue_file)
        revenue_agg = revenue_df.groupby("campid")["estimated_revenue"].sum().reset_index()
        revenue_agg.rename(columns={"estimated_revenue": "Revenue"}, inplace=True)
        revenue_agg["CampID"] = revenue_agg["campid"].astype(int)
        revenue_agg.drop(columns=["campid"], inplace=True)

        # --- Load spend file (header starts at row index 2 = third row visually) ---
        spend_df = pd.read_excel(spend_file, header=2)

        if "Campaign" not in spend_df.columns or "Cost" not in spend_df.columns:
            st.error("❌ 'Campaign' or 'Cost' column not found in the uploaded Excel file.")
            st.dataframe(spend_df.head(10))
        else:
            # Extract Campaign Name & ID
            spend_df["Campaign Name"] = spend_df["Campaign"]
            spend_df["CampID"] = spend_df["Campaign Name"].astype(str).str.extract(r"\((\d+)\)")
            spend_df = spend_df[spend_df["CampID"].notnull()]  # Drop rows without campaign ID
            spend_df["CampID"] = spend_df["CampID"].astype(int)

            # Extract Spend
            spend_df["Spend"] = pd.to_numeric(spend_df["Cost"], errors="coerce")
            spend_clean = spend_df[["CampID", "Campaign Name", "Spend"]]

            # --- Merge with revenue and calculate Profit/Loss ---
            merged = pd.merge(spend_clean, revenue_agg, on="CampID", how="left")
            merged["Revenue"] = merged["Revenue"].fillna(0)
            merged["Profit/Loss"] = merged["Revenue"] - merged["Spend"]

            # Reorder columns
            merged = merged[["CampID", "Campaign Name", "Spend", "Revenue", "Profit/Loss"]]

            # --- Display Results ---
            st.subheader("📈 Profit / Loss Report")
            st.dataframe(merged, use_container_width=True)

            # --- Download CSV ---
            csv = merged.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "campaign_profit_loss.csv", "text/csv")

    except Exception as e:
        st.error(f"🚨 An error occurred: {e}")
