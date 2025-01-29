import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import google.generativeai as genai  # Import the google-generativeai module


# Load environment variables
load_dotenv()

# OKTA and JIRA Configuration
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

# API Headers
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Function to interact with Gemini

def prompt_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    request_options={"timeout": 600}
    return response.text

# Function to create a JIRA issue
def create_jira_issue(summary, description, issue_type="Task", parent_key=None):
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "text": description,
                        "type": "text"
                    }]
                }]
            },
            "issuetype": {"name": issue_type}
        }
    }
    if parent_key:
        payload["fields"]["parent"] = {"key": parent_key}
    
    response = requests.post(url, headers=headers, auth=(JIRA_EMAIL, JIRA_API_TOKEN), data=json.dumps(payload))
    if response.status_code == 201:
        return response.json()["key"]
    return None

# Streamlit UI
st.title("JIRA Issue Management with ServiceNow Integration")

with st.form("issue_form"):
    title = st.text_input("Issue Title")
    description = st.text_area("Issue Description")
    submit_button = st.form_submit_button("Create Cluster")

if submit_button:
    if title and description:
        cluster_summary = prompt_gemini(f"Summarize this issue: {title}")
        cluster_description = prompt_gemini(f"Summarize this description: {description}")
        
        parent_key = create_jira_issue(cluster_summary, cluster_description)
        if parent_key:
            st.success(f"Cluster Created Successfully! Parent Issue Key: {parent_key}")
        else:
            st.error("Failed to create cluster")
    else:
        st.error("Please fill in both title and description fields.")
