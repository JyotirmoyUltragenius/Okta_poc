import os
import json
import requests
from flask import Flask, jsonify
from datetime import datetime, timedelta

# ✅ OKTA CONFIGURATION (Embedded)
OKTA_CONFIG = {
    "domain": "https://<your-okta-domain>.okta.com",
    "client_id": os.getenv("OKTA_CLIENT_ID", "<your-client-id>"),
    "client_secret": os.getenv("OKTA_CLIENT_SECRET", "<your-client-secret>"),
    "authorization_server_id": "<your-authorization-server-id>",
    "token_endpoint": "/oauth2/default/v1/token",
    "scopes": ["openid", "profile", "email"],
    "grant_type": "client_credentials",
    "cache_duration": 3600
}

TOKEN_CACHE = {
    "access_token": None,
    "expiry": datetime.utcnow()
}

app = Flask(__name__)

# ✅ FUNCTION TO GET OKTA TOKEN
def get_okta_token():
    global TOKEN_CACHE

    # Check if cached token is still valid
    if TOKEN_CACHE["access_token"] and TOKEN_CACHE["expiry"] > datetime.utcnow():
        return TOKEN_CACHE["access_token"]

    # Request new token
    url = OKTA_CONFIG["domain"] + OKTA_CONFIG["token_endpoint"]
    payload = {
        "grant_type": OKTA_CONFIG["grant_type"],
        "client_id": OKTA_CONFIG["client_id"],
        "client_secret": OKTA_CONFIG["client_secret"],
        "scope": " ".join(OKTA_CONFIG["scopes"])
    }

    response = requests.post(url, data=payload)
    response.raise_for_status()
    token_data = response.json()

    # Cache new token with expiry
    TOKEN_CACHE["access_token"] = token_data["access_token"]
    TOKEN_CACHE["expiry"] = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

    return token_data["access_token"]

# ✅ API ENDPOINT TO FETCH DATA
@app.route('/api/data', methods=['GET'])
def fetch_data():
    try:
        token = get_okta_token()

        # Replace with your actual API endpoint
        api_url = "https://api.example.com/resource"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        return jsonify({"status": "success", "data": response.json()})
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ HEALTH CHECK ENDPOINT
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

# ✅ MAIN ENTRY POINT
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
