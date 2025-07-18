import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import json
import uuid

st.set_page_config(page_title="💸 BudgetGuru", layout="centered")

# ========== GLOBAL CONFIG ==========
SHEET_NAME = "BudgetGuruApp"
USER_ID = st.session_state.get("user_id", str(uuid.uuid4()))  # Unique per session/device
st.session_state["user_id"] = USER_ID  # Persist for session

# ========== GOOGLE SHEETS AUTH ==========
def connect_to_gsheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

# ========== SETUP ==========
sheet = connect_to_gsheet()

# Auto-create headers if empty
if sheet.row_count < 1 or not sheet.get_all_values():
    sheet.update('A1:E1', [["Timestamp", "UserID", "Date", "Category", "Amount"]])
    sheet.update('G1:H1', [["UserID", "Budget"]])

# ========== BUDGET ==========
st.title("💸 Set Weekly Budget")
budget_input = st.number_input("Enter weekly budget (₹)", min_value=0, step=100)

if st.button("Set Budget"):
    try:
        existing_user_ids = sheet.col_values(7)  # Col G
        if USER_ID in existing_user_ids:
            row_idx = existing_user_ids.index(USER_ID) + 1
            sheet.update(f"H{row_idx}", [[budget_input]])
        else:
            sheet.append_row(["", "", "", "", "", "", USER_ID, budget_input])
        st.success("✅ Budget set successfully!")
    except Exception as e:
        st.error(f"⚠️ Failed to save budget: {e}")

# ========== ADD EXPENSE ==========
st.header("➕ Add Expense")
expense_date = st.date_input("Date", value=datetime.today())

main_category = st.selectbox("Main Category", ["Food", "Bills", "Shopping", "Transport", "Entertainment"])
subcategory_options = {
    "Food": ["Breakfast", "Lunch", "Dinner", "Snacks", "Groceries"],
    "Bills": ["Electricity", "Water", "Internet", "Rent", "EMI"],
    "Shopping": ["Clothes", "Electronics", "Online"],
    "Transport": ["Bus", "Train", "Taxi", "Fuel"],
    "Entertainment": ["Movies", "Games", "Streaming"]
}
sub_category = st.selectbox("Subcategory", subcategory_options[main_category])  # type: ignore
amount = st.number_input("Amount (₹)", min_value=0, step=50)

if st.button("Add Expense"):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, USER_ID, str(expense_date), f"{main_category} → {sub_category}", amount])
        st.success("✅ Expense added!")
    except Exception as e:
        st.error(f"⚠️ Failed to add expense: {e}")

# ========== WEEKLY SUMMARY ==========
st.header("📊 Weekly Summary")

data = sheet.get_all_records()
df = pd.DataFrame(data)
user_df = df[df["UserID"] == USER_ID]

if not user_df.empty:
    total_spent = user_df["Amount"].sum()
    user_budget_row = df[df["UserID"] == USER_ID]
    budget = user_budget_row["Budget"].values[0] if not user_budget_row["Budget"].isnull().all() else 0
    remaining = max(budget - total_spent, 0)

    st.metric("💸 Total Spent", f"₹{total_spent}")
    st.metric("✅ Remaining Budget", f"₹{remaining}")
else:
    st.info("ℹ️ No expenses added yet.")

# ========== RESET BUTTON ==========
st.markdown("---")
if st.button("🗑️ Reset App"):
    try:
        all_data = sheet.get_all_records()
        new_data = [row for row in all_data if row["UserID"] != USER_ID]
        new_data.insert(0, ["Timestamp", "UserID", "Date", "Category", "Amount"])
        sheet.clear()
        sheet.update("A1", new_data)

        # Clear budget row too
        all_rows = sheet.get_all_values()
        remaining_rows = [row for row in all_rows if len(row) < 7 or row[6] != USER_ID]
        sheet.clear()
        if remaining_rows:
            sheet.update("A1", remaining_rows)

        st.success("✅ App reset successfully.")
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Failed to reset app: {e}")
