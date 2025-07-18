import streamlit as st
from datetime import datetime, date
import pandas as pd
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------- GOOGLE SHEETS SETUP --------------------
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["GOOGLE_SHEETS_CREDS"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("BudgetGuruApp")
    return spreadsheet.worksheet("Expenses"), spreadsheet.worksheet("Budgets")

expense_sheet, budget_sheet = connect_to_gsheet()

# -------------------- USER IDENTIFICATION --------------------
user_id = st.text_input("Enter your name or ID (required):", key="user_id_input")
if not user_id:
    st.warning("Please enter your name or ID to continue.")
    st.stop()

# -------------------- SESSION STATE INIT --------------------
if "weekly_budget" not in st.session_state:
    st.session_state.weekly_budget = None
if "expenses_df" not in st.session_state:
    st.session_state.expenses_df = pd.DataFrame(columns=["Timestamp", "UserID", "Date", "Category", "Amount (₹)"])

# -------------------- CATEGORY OPTIONS --------------------
category_options = {
    "Food": ["Lunch", "Dinner", "Snacks"],
    "Bills": ["Electricity", "Water", "Internet"],
    "Shopping": ["Clothing", "Electronics", "Groceries"],
    "Other": ["Entertainment", "Transport", "Misc"]
}

# -------------------- HEADER --------------------
st.title("💰 BudgetGuru – Personal Expense Tracker")

# -------------------- BUDGET SETUP --------------------
with st.expander("📝 Set Weekly Budget"):
    budget_input = st.number_input("Enter your weekly budget (₹):", min_value=0)
    if st.button("✅ Save Weekly Budget"):
        # Save to Google Sheet
        existing_users = budget_sheet.col_values(1)
        if user_id in existing_users:
            row_index = existing_users.index(user_id) + 1
            budget_sheet.update(f"B{row_index}", budget_input)
        else:
            budget_sheet.append_row([user_id, budget_input])
        st.success("Weekly budget saved!")
        st.session_state.weekly_budget = budget_input

# -------------------- LOAD EXISTING BUDGET --------------------
def load_user_budget():
    records = budget_sheet.get_all_records()
    for row in records:
        if row["UserID"] == user_id:
            return float(row["Budget"])
    return None

if st.session_state.weekly_budget is None:
    st.session_state.weekly_budget = load_user_budget()

# -------------------- EXPENSE ENTRY --------------------
st.subheader("➕ Add Expense")

today = date.today()
selected_main = st.selectbox("Category", list(category_options.keys()))
selected_sub = st.selectbox("Subcategory", category_options[selected_main])
expense_amount = st.number_input("Amount (₹)", min_value=1)
expense_date = st.date_input("Date", value=today)

if st.button("💾 Add Expense"):
    new_row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, expense_date.strftime("%Y-%m-%d"), f"{selected_main} → {selected_sub}", expense_amount]
    expense_sheet.append_row(new_row)
    st.success("Expense added successfully!")

# -------------------- LOAD EXPENSES --------------------
@st.cache_data(ttl=300)
def load_expenses():
    data = expense_sheet.get_all_records(expected_headers=["Timestamp", "UserID", "Date", "Category", "Amount", "UserID", "Budget"])
    return pd.DataFrame(data)

df = load_expenses()
user_df = df[df["UserID"] == user_id]

# -------------------- WEEKLY SUMMARY --------------------
st.subheader("📊 Weekly Summary")
if not user_df.empty:
    user_df["Amount (₹)"] = pd.to_numeric(user_df["Amount (₹)"], errors='coerce').fillna(0)
    total_spent = user_df["Amount (₹)"].sum()
    remaining = st.session_state.weekly_budget - total_spent if st.session_state.weekly_budget else 0

    col1, col2 = st.columns(2)
    col1.metric("Total Spent", f"₹{total_spent:.2f}")
    col2.metric("Remaining Budget", f"₹{remaining:.2f}")

    # Color indicator
    if remaining < st.session_state.weekly_budget * 0.2:
        st.warning("⚠️ Your remaining budget is less than 20%. Consider reducing spending.")
    else:
        st.success("✅ You're managing your budget well!")

    # Expense table
    st.dataframe(user_df[["Date", "Category", "Amount (₹)"]], use_container_width=True)
else:
    st.info("No expenses found for this user yet.")

# -------------------- RESET FUNCTION --------------------
st.markdown("---")
if st.button("🧹 Reset My Data"):
    # Remove all user rows from both sheets
    df_all = df
    rows_to_delete = df_all[df_all["UserID"] == user_id].index.tolist()
    rows_to_delete = [i + 2 for i in rows_to_delete]  # +2 accounts for header row + 1-indexing
    for i in sorted(rows_to_delete, reverse=True):
        expense_sheet.delete_row(i)

    budget_records = budget_sheet.get_all_records()
    for idx, row in enumerate(budget_records):
        if row["UserID"] == user_id:
            budget_sheet.delete_row(idx + 2)
            break

    # Clear local session
    st.session_state.weekly_budget = None
    st.session_state.expenses_df = pd.DataFrame()
    st.success("✅ Your data has been reset. You can start fresh.")

