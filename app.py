import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pandas as pd

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

uploaded_file = st.file_uploader("Upload ServiceNow CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write(df.head())

    cluster_options = df['cluster'].unique().tolist()
    cluster_choice = st.selectbox("Select Cluster", cluster_options)
    cluster_df = df[df['cluster'] == cluster_choice]

    if st.button("Create JIRA Issues"):
        ticket_ids = cluster_df['Ticket ID'].tolist()
        ticket_titles = ', '.join(cluster_df['Title'].tolist())
        summary = prompt_gemini(f"Summarize these tickets: {ticket_titles}")
        
        descriptions = '\n'.join(cluster_df['Description'].tolist())
        description_summary = prompt_gemini(f"Summarize these descriptions: {descriptions}")
        
        parent_key = create_jira_issue(summary, description_summary)
        if parent_key:
            st.success(f"Created Parent Issue: {parent_key}")
            for index, row in cluster_df.iterrows():
                subtask_summary = row['Title']
                subtask_description = row['Description']
                subtask_key = create_jira_issue(subtask_summary, subtask_description, "Subtask", parent_key)
                if subtask_key:
                    st.write(f"Subtask Created: {subtask_key}")
                else:
                    st.error("Failed to create subtask")
        else:
            st.error("Failed to create parent issue")
