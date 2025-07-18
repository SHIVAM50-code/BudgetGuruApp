import streamlit as st
import pandas as pd
import datetime
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="💰 BudgetGuru", layout="centered")

# ---- Google Sheets Setup ----
def connect_to_gsheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("BudgetGuruApp").sheet1  # Make sure sheet name matches
    return sheet

# ---- Budget Management ----
def read_budget(sheet):
    try:
        return int(sheet.acell('B1').value)
    except:
        return 0

def write_budget(sheet, amount):
    sheet.update('A1', 'Budget')
    sheet.update('B1', str(amount))

# ---- Add new expense to sheet ----
def add_expense_to_sheet(sheet, date, category, amount):
    row = [str(date), category, amount]
    sheet.append_row(row)

# ---- Load existing expenses (skip first row which holds budget) ----
def load_expenses(sheet):
    records = sheet.get_all_records()
    return pd.DataFrame(records)

# ---- App Layout ----
st.title("💰 BudgetGuru – Personal Expense Tracker")

# ---- Connect to Sheet ----
sheet = connect_to_gsheet()

# ---- Read Persistent Budget ----
if "weeklybudget" not in st.session_state:
    st.session_state.weeklybudget = read_budget(sheet)

st.subheader("📅 Weekly Budget")
st.info(f"Your current saved budget is ₹{st.session_state.weeklybudget}")

# ---- Option to update budget ----
budget_input = st.number_input("Update your budget (optional)", min_value=0, step=100)
if st.button("Update Budget"):
    write_budget(sheet, budget_input)
    st.session_state.weeklybudget = budget_input
    st.success(f"✅ Budget updated to ₹{budget_input}")

st.markdown("---")

# ---- Expense Entry ----
st.subheader("➕ Add an Expense")

expense_date = st.date_input("🗓️ Date", value=datetime.date.today())
main_category = st.selectbox("Main Category", ["Food", "Bills", "Shopping", "Entertainment", "Transport", "Health", "Other"])

subcategories = {
    "Food": ["Breakfast", "Lunch", "Dinner", "Snacks", "Other"],
    "Bills": ["Electricity", "Internet", "Gas", "Water", "Other"],
    "Shopping": ["Clothes", "Electronics", "Groceries", "Other"],
    "Entertainment": ["Movies", "Games", "Subscription", "Other"],
    "Transport": ["Bus", "Train", "Fuel", "Taxi", "Other"],
    "Health": ["Medicine", "Doctor Visit", "Insurance", "Other"],
    "Other": ["Miscellaneous"]
}

subcategory = st.selectbox("Subcategory", subcategories[main_category])

# Combine both for saving to Google Sheet
category = f"{main_category} - {subcategory}"

amount = st.number_input("💸 Amount (₹)", min_value=1, step=1)

if st.button("Add Expense"):
    add_expense_to_sheet(sheet, expense_date, category, amount)
    st.success("✅ Expense added successfully!")

st.markdown("---")

# ---- Summary ----
st.subheader("📊 Weekly Summary")

expenses_df = load_expenses(sheet)

if not expenses_df.empty:
    st.dataframe(expenses_df, use_container_width=True)

    if "Amount (₹)" in expenses_df.columns:
        total_spent = expenses_df["Amount (₹)"].sum()
        remaining = st.session_state.weeklybudget - total_spent

        st.metric("Total Spent", f"₹{total_spent}")
        st.metric("Remaining Budget", f"₹{remaining}")

        if remaining < st.session_state.weeklybudget * 0.2:
            st.warning("⚠️ You're about to exceed your budget. Consider reducing expenses!")
        elif remaining > st.session_state.weeklybudget * 0.6:
            st.success("✅ Great! You're managing your expenses well.")
        else:
            st.info("📈 Keep tracking to stay within your limits.")
    else:
        st.warning("⚠️ Amount (₹) column not found in sheet.")
else:
    st.info("No expenses added yet.")
