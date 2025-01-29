import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
import google.api_core.exceptions

# Load environment variables
load_dotenv()

# OKTA and JIRA Configuration
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

# Configure the generative AI client
genai.configure(api_key=GENAI_API_KEY)

# API Headers
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Function to interact with Gemini with retries
def prompt_gemini(prompt, max_retries=5):
    model = genai.GenerativeModel(model="models/gemini-1.5-flash")
    delay = 1  # Initial delay in seconds
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt, request_options={"timeout": 600})
            return response.text
        except google.api_core.exceptions.DeadlineExceeded as e:
            st.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
    st.error("Max retries exceeded while trying to connect to Gemini API.")
    return ""

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
        
        if cluster_summary and cluster_description:
            parent_key = create_jira_issue(cluster_summary, cluster_description)
            if parent_key:
                st.success(f"Cluster Created Successfully! Parent Issue Key: {parent_key}")
            else:
                st.error("Failed to create cluster")
        else:
            st.error("Failed to generate cluster summary or description from Gemini API.")
    else:
        st.error("Please fill in both title and description fields.")
