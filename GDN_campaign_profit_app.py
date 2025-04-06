import streamlit as st
import pandas as pd
import re

# Streamlit settings
st.set_page_config(page_title="Campaign Revenue vs Spend Analyzer", layout="centered")
st.title("📊 Campaign Revenue vs Spend Analyzer 💰 (Live from Google Sheets)")

# ✅ LIVE Revenue Sheet URL (Google Sheets CSV export)
REVENUE_SHEET_URL = "https://ocs.google.com/spreadsheets/d/e/2PACX-1vRnfJUyX9TOWkRHgJivH4U6-o83t9nM9hRkC2zbH_p0tsl3D2kH0ak54iZBNcDO60Ygbp7CRMP7hLzX/pub?gid=0&single=true&output=csv"

# Upload spend Excel file
spend_file = st.file_uploader("Upload Spend Excel File", type=["xlsx"])

if spend_file:
    try:
        # ✅ Load live revenue data from Google Sheets
        revenue_df = pd.read_csv(REVENUE_SHEET_URL)
        revenue_agg = revenue_df.groupby("campid")["estimated_revenue"].sum().reset_index()
        revenue_agg.rename(columns={"estimated_revenue": "Revenue"}, inplace=True)
        revenue_agg["CampID"] = revenue_agg["campid"].astype(int)
        revenue_agg.drop(columns=["campid"], inplace=True)

        # ✅ Load spend Excel file (headers start on row 3, i.e., index 2)
        spend_df = pd.read_excel(spend_file, header=2)

        # Ensure required columns exist
        if "Campaign" not in spend_df.columns or "Cost" not in spend_df.columns:
            st.error("❌ 'Campaign' or 'Cost' column not found in the uploaded Excel file.")
            st.dataframe(spend_df.head(10))
        else:
            # Extract campaign info
            spend_df["Campaign Name"] = spend_df["Campaign"]
            spend_df["CampID"] = spend_df["Campaign Name"].astype(str).str.extract(r"\((\d+)\)")
            spend_df = spend_df[spend_df["CampID"].notnull()]  # Drop rows without ID
            spend_df["CampID"] = spend_df["CampID"].astype(int)

            # Clean cost
            spend_df["Spend"] = pd.to_numeric(spend_df["Cost"], errors="coerce")

            # Prepare spend data
            spend_clean = spend_df[["CampID", "Campaign Name", "Spend"]]

            # Merge with live revenue
            merged = pd.merge(spend_clean, revenue_agg, on="CampID", how="left")
            merged["Revenue"] = merged["Revenue"].fillna(0)
            merged["Profit/Loss"] = merged["Revenue"] - merged["Spend"]

            # Reorder columns
            final_df = merged[["CampID", "Campaign Name", "Spend", "Revenue", "Profit/Loss"]]

            # Show results
            st.subheader("📈 Profit / Loss Report")
            st.dataframe(final_df, use_container_width=True)

            # Download as CSV
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "campaign_profit_loss.csv", "text/csv")

    except Exception as e:
        st.error(f"🚨 Error: {e}")
