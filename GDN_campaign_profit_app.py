import streamlit as st
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import pandas as pd

# --------- Streamlit Setup ---------
st.set_page_config(page_title="Google Ads MCC Spend Viewer", layout="centered")
st.title("📊 Google Ads Manager - Account Spend Overview")

# --------- Load credentials from Streamlit secrets ---------
config = {
    "developer_token": st.secrets["GOOGLE_ADS_DEVELOPER_TOKEN"],
    "client_id": st.secrets["GOOGLE_ADS_CLIENT_ID"],
    "client_secret": st.secrets["GOOGLE_ADS_CLIENT_SECRET"],
    "refresh_token": st.secrets["GOOGLE_ADS_REFRESH_TOKEN"],
    "use_proto_plus": True
}

# --------- Initialize Google Ads Client ---------
try:
    client = GoogleAdsClient.load_from_dict(config)
    customer_service = client.get_service("CustomerService")
    st.success("✅ Connected to Google Ads API")
except Exception as e:
    st.error(f"❌ Failed to connect to Google Ads API: {e}")
    st.stop()

# --------- Get list of customer accounts ---------
accounts = customer_service.list_accessible_customers()
customer_ids = [res.split("/")[-1] for res in accounts.resource_names]

# --------- Build query to fetch last 7 days spend ---------
query = """
    SELECT
      customer.id,
      customer.descriptive_name,
      metrics.cost_micros
    FROM customer
    WHERE segments.date DURING LAST_7_DAYS
"""

# --------- Pull spend for each account ---------
spend_data = []

for cid in customer_ids:
    try:
        ga_service = client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=cid, query=query)

        for row in response:
            spend_data.append({
                "Customer ID": row.customer.id,
                "Account Name": row.customer.descriptive_name,
                "Spend (USD)": row.metrics.cost_micros / 1_000_000
            })

    except GoogleAdsException as e:
        st.warning(f"⚠️ Could not access customer {cid}: {e}")

# --------- Display in Streamlit ---------
if spend_data:
    df = pd.DataFrame(spend_data)
    df = df.sort_values(by="Spend (USD)", ascending=False)

    st.subheader("💰 Account Spend - Last 7 Days")
    st.dataframe(df, use_container_width=True)

    # Optional download button
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "account_spend.csv", "text/csv")
else:
    st.info("No spend data available from linked accounts.")
