import streamlit as st
import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# ---------------------------
# STREAMLIT SETUP
# ---------------------------
st.set_page_config(page_title="Google Ads MCC Spend", layout="centered")
st.title("📊 Google Ads Manager - Account Spend Overview")

# ---------------------------
# GOOGLE ADS CLIENT CONFIG
# ---------------------------
config = {
    "developer_token": st.secrets["GOOGLE_ADS_DEVELOPER_TOKEN"],
    "client_id": st.secrets["GOOGLE_ADS_CLIENT_ID"],
    "client_secret": st.secrets["GOOGLE_ADS_CLIENT_SECRET"],
    "refresh_token": st.secrets["GOOGLE_ADS_REFRESH_TOKEN"],
    "login_customer_id": "5003253105",  # 👈 Your MCC ID
    "use_proto_plus": True
}

try:
    client = GoogleAdsClient.load_from_dict(config)
    st.success("✅ Connected to Google Ads API")
except Exception as e:
    st.error(f"❌ Failed to connect to Google Ads API: {e}")
    st.stop()

# ---------------------------
# CUSTOMER IDS TO QUERY
# ---------------------------
customer_ids = [
    "9126180247",  # AppD - 2 KS
    "6099598182",  # AppD - 1 LegitLevel
    "8583652603",  # AppD - 6 Knowledgesharer
    "9195646607",  # AppD - 7 Knowledgesharer
    "6597133033",  # AppD - 8 LegitLevel
]

# ---------------------------
# QUERY FOR LAST 7 DAYS SPEND
# ---------------------------
query = """
    SELECT
      customer.id,
      customer.descriptive_name,
      metrics.cost_micros
    FROM customer
    WHERE segments.date DURING LAST_7_DAYS
"""

spend_data = []

for cid in customer_ids:
    try:
        ga_service = client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=cid, query=query)

        for row in response:
            spend_data.append({
                "Customer ID": row.customer.id,
                "Account Name": row.customer.descriptive_name,
                "Spend (USD)": round(row.metrics.cost_micros / 1_000_000, 2)
            })

    except GoogleAdsException as e:
        st.warning(f"⚠️ Error accessing {cid}: {e.error.code().name}")

# ---------------------------
# DISPLAY RESULTS
# ---------------------------
if spend_data:
    df = pd.DataFrame(spend_data)
    df = df.sort_values(by="Spend (USD)", ascending=False)

    st.subheader("💰 Last 7 Days Spend by Account")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "account_spend.csv", "text/csv")
else:
    st.info("No spend data retrieved from selected accounts.")
