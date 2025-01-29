import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ✅ OKTA CONFIGURATION
OKTA_CONFIG = {
    "domain": os.getenv("OKTA_DOMAIN", "https://<your-okta-domain>.okta.com"),
    "client_id": os.getenv("OKTA_CLIENT_ID", "<your-client-id>"),
    "client_secret": os.getenv("OKTA_CLIENT_SECRET", "<your-client-secret>"),
    "authorization_server_id": os.getenv("OKTA_AUTH_SERVER_ID", "<your-auth-server-id>"),
    "token_endpoint": os.getenv("OKTA_TOKEN_ENDPOINT", "/oauth2/default/v1/token"),
}

TOKEN_CACHE_FILE = "okta_token.json"
EXPIRY_BUFFER = 300  # Request new token if it's about to expire in 5 mins


# ✅ Function to Fetch Token
def get_okta_token():
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r") as f:
            token_data = json.load(f)
            expiry_time = datetime.fromisoformat(token_data["expiry"]).replace(tzinfo=timezone.utc)
            if expiry_time > datetime.now(timezone.utc) + timedelta(seconds=EXPIRY_BUFFER):
                return token_data["access_token"]

    # Fetch a new token
    url = OKTA_CONFIG["domain"] + OKTA_CONFIG["token_endpoint"]
    payload = {
        "grant_type": "client_credentials",
        "client_id": OKTA_CONFIG["client_id"],
        "client_secret": OKTA_CONFIG["client_secret"],
        "scope": "openid profile email",
    }
    
    response = requests.post(url, data=payload)
    response.raise_for_status()
    token_data = response.json()
    token_data["expiry"] = (datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])).isoformat()

    # Cache token
    with open(TOKEN_CACHE_FILE, "w") as f:
        json.dump(token_data, f)

    return token_data["access_token"]


# ✅ Streamlit UI
st.title("🔐 Okta-Authenticated API")

# Fetch token button
if st.button("Get Okta Token"):
    try:
        token = get_okta_token()
        st.success("✅ Token fetched successfully!")
        st.code(token, language="plaintext")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# API Request section
st.subheader("🌍 Fetch Protected API Data")
api_url = st.text_input("Enter API URL:", "https://api.example.com/resource")

if st.button("Fetch Data"):
    token = get_okta_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        st.json(response.json())  # Display JSON response
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Request Failed: {str(e)}")

st.write("🚀 Developed with Streamlit & Okta")

