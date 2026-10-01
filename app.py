import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Jira Bulk Updater", page_icon="⚙️️", layout="wide")

st.title("⚙️ Jira Bulk Issue Updater")
st.markdown("Upload a CSV file, map your columns to Jira fields, and process updates safely.")

# Sidebar Configuration
st.sidebar.header("🔑 Authentication & Config")
jira_url = st.sidebar.text_input("Jira Base URL", value="https://onejira.verizon.com")
api_token = st.sidebar.text_input("Jira API Token", type="password", help="Your Jira Bearer Token or Personal Access Token")

update_action = st.sidebar.selectbox(
    "Select Action Type",
    ["Update Issue Fields (Summary, Description, etc.)", "Link Issues", "Add Comments"]
)

# Step 1: File Upload
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file and api_token and jira_url:
    # Read CSV
    df = pd.read_csv(uploaded_file, dtype=str).fillna("")
    st.subheader("1. Preview CSV Data")
    st.dataframe(df.head(5), use_container_width=True)

    csv_columns = ["-- Select Column --"] + list(df.columns)
    
    st.subheader("2. Configure Column Mapping")
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Action 1: Update Fields (Summary, etc.)
    if update_action == "Update Issue Fields (Summary, Description, etc.)":
        col1, col2 = st.columns(2)
        with col1:
            key_col = st.selectbox("Issue Key Column *", csv_columns, index=0)
        with col2:
            summary_col = st.selectbox("New Summary Column (Optional)", csv_columns, index=0)

        if st.button("🚀 Process Bulk Field Update", type="primary"):
            if key_col == "-- Select Column --":
                st.error("Please select an Issue Key column.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.container()

                total_rows = len(df)
                success_count = 0

                for idx, row in df.iterrows():
                    issue_key = row[key_col].strip()
                    if not issue_key:
                        continue

                    payload = {"fields": {}}
                    if summary_col != "-- Select Column --" and row[summary_col].strip():
                        payload["fields"]["summary"] = row[summary_col].strip()

                    if not payload["fields"]:
                        log_container.warning(f"Row {idx+1} ({issue_key}): Skipped (No fields to update)")
                        continue

                    url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{issue_key}"
                    
                    try:
                        res = requests.put(url, json=payload, headers=headers)
                        if res.status_code == 204:
                            success_count += 1
                            log_container.success(f"Row {idx+1}: Updated {issue_key}")
                        else:
                            log_container.error(f"Row {idx+1}: Failed {issue_key} - HTTP {res.status_code}: {res.text}")
                    except Exception as e:
                        log_container.error(f"Row {idx+1}: Error updating {issue_key}: {e}")

                    progress_bar.progress((idx + 1) / total_rows)
                    status_text.text(f"Processed {idx + 1}/{total_rows} rows...")

                st.success(f"Completed! Successfully updated {success_count}/{total_rows} issues.")

    # Action 2: Link Issues
    elif update_action == "Link Issues":
        col1, col2, col3 = st.columns(3)
        with col1:
            from_col = st.selectbox("From / Source Issue Key Column *", csv_columns, index=0)
        with col2:
            to_col = st.selectbox("To / Target Issue Key Column *", csv_columns, index=0)
        with col3:
            type_col = st.selectbox("Link Type Column (Optional)", csv_columns, index=0)
            default_link_type = st.text_input("Default Link Type if unmapped/empty", value="Relates")

        if st.button("🚀 Process Bulk Issue Linking", type="primary"):
            if from_col == "-- Select Column --" or to_col == "-- Select Column --":
                st.error("Please select both 'From' and 'To' Issue Key columns.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.container()

                total_rows = len(df)
                success_count = 0

                for idx, row in df.iterrows():
                    from_issue = row[from_col].strip()
                    to_issue = row[to_col].strip()
                    link_type = row[type_col].strip() if type_col != "-- Select Column --" and row[type_col].strip() else default_link_type

                    if not from_issue or not to_issue:
                        log_container.warning(f"Row {idx+1}: Skipped (Missing source or target issue key)")
                        continue

                    url = f"{jira_url.rstrip('/')}/rest/api/2/issueLink"
                    payload = {
                        "type": {"name": link_type},
                        "inwardIssue": {"key": to_issue},
                        "outwardIssue": {"key": from_issue}
                    }

                    try:
                        res = requests.post(url, json=payload, headers=headers)
                        if res.status_code == 201:
                            success_count += 1
                            log_container.success(f"Row {idx+1}: Linked '{from_issue}' {link_type.lower()} '{to_issue}'")
                        else:
                            log_container.error(f"Row {idx+1}: Failed linking '{from_issue}' -> '{to_issue}': HTTP {res.status_code} - {res.text}")
                    except Exception as e:
                        log_container.error(f"Row {idx+1}: Error linking '{from_issue}' -> '{to_issue}': {e}")

                    progress_bar.progress((idx + 1) / total_rows)
                    status_text.text(f"Processed {idx + 1}/{total_rows} rows...")

                st.success(f"Completed! Successfully linked {success_count}/{total_rows} issue pairs.")

    # Action 3: Add Comments
    elif update_action == "Add Comments":
        col1, col2 = st.columns(2)
        with col1:
            key_col = st.selectbox("Issue Key Column *", csv_columns, index=0)
        with col2:
            comment_col = st.selectbox("Comment Text Column *", csv_columns, index=0)

        if st.button("🚀 Process Bulk Comments", type="primary"):
            if key_col == "-- Select Column --" or comment_col == "-- Select Column --":
                st.error("Please select both Issue Key and Comment columns.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.container()

                total_rows = len(df)
                success_count = 0

                for idx, row in df.iterrows():
                    issue_key = row[key_col].strip()
                    comment_text = row[comment_col].strip()

                    if not issue_key or not comment_text:
                        log_container.warning(f"Row {idx+1}: Skipped (Missing Issue Key or Comment text)")
                        continue

                    url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{issue_key}/comment"
                    payload = {"body": comment_text}

                    try:
                        res = requests.post(url, json=payload, headers=headers)
                        if res.status_code == 201:
                            success_count += 1
                            log_container.success(f"Row {idx+1}: Added comment to {issue_key}")
                        else:
                            log_container.error(f"Row {idx+1}: Failed commenting on {issue_key}: HTTP {res.status_code} - {res.text}")
                    except Exception as e:
                        log_container.error(f"Row {idx+1}: Error commenting on {issue_key}: {e}")

                    progress_bar.progress((idx + 1) / total_rows)
                    status_text.text(f"Processed {idx + 1}/{total_rows} rows...")

                st.success(f"Completed! Successfully commented on {success_count}/{total_rows} issues.")

else:
    st.info("👆 Please enter your Jira Token in the sidebar and upload a CSV file to get started.")
