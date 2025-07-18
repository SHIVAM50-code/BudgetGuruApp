import streamlit as st
import pandas as pd
from datetime import date
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------- Google Sheets Setup ----------
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("BudgetGuruApp").sheet1
    return sheet

def initialize_sheet_headers(sheet):
    try:
        current_headers = sheet.row_values(1)
        required_headers = ["Date", "Category", "Subcategory", "Amount (₹)"]
        if not current_headers or current_headers != required_headers:
            sheet.update("A1:D1", [required_headers])
    except Exception as e:
        st.error(f"❌ Error initializing headers: {e}")

def add_expense_to_sheet(sheet, expense_date, category, sub_category, amount):
    try:
        row = [str(expense_date), category, sub_category, amount]
        sheet.append_row(row)
    except Exception as e:
        st.error(f"❌ Failed to log expense: {e}")

def get_all_data(sheet):
    try:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Date", "Category", "Subcategory", "Amount (₹)"])

# ---------- Streamlit App ----------
st.set_page_config(page_title="💰 BudgetGuru", layout="centered")
st.title("💸 BudgetGuru – Personal Expense Tracker")

sheet = connect_to_gsheet()
initialize_sheet_headers(sheet)

# --------- Weekly Budget Setup ---------
if "weekly_budget" not in st.session_state:
    sheet_data = get_all_data(sheet)
    if not sheet_data.empty and "Budget" in sheet_data.columns:
        st.session_state.weekly_budget = float(sheet_data["Budget"].iloc[0])
    else:
        st.session_state.weekly_budget = 0

st.subheader("🗓️ Set Weekly Budget")
budget_input = st.number_input("Enter weekly budget (₹)", min_value=0, step=100, value=st.session_state.weekly_budget)
if st.button("Set Budget"):
    st.session_state.weekly_budget = budget_input
    try:
        sheet.update("A2", "Budget")
        sheet.update("D2", budget_input)
        st.success("✅ Budget saved successfully!")
    except Exception as e:
        st.warning(f"⚠️ Failed to save budget: {e}")

# --------- Expense Input ---------
st.subheader("🧾 Log New Expense")

expense_date = st.date_input("Date", value=date.today())

category_options = {
    "Food": ["Lunch", "Dinner", "Snacks", "Groceries"],
    "Bills": ["Electricity", "Water", "Phone", "Internet", "Gas"],
    "Shopping": ["Clothes", "Accessories", "Online Orders"],
    "Transport": ["Bus", "Metro", "Cab", "Petrol"],
    "Entertainment": ["Movies", "Games", "Subscriptions"]
}

main_category = st.selectbox("Category", list(category_options.keys()))
sub_category = st.selectbox("Subcategory", category_options[main_category])
amount = st.number_input("Amount Spent (₹)", min_value=0, step=10)

if st.button("Add Expense"):
    add_expense_to_sheet(sheet, expense_date, main_category, sub_category, amount)
    st.success("✅ Expense added successfully!")

# --------- Summary ---------
st.subheader("📊 Weekly Summary")

df = get_all_data(sheet)
if not df.empty:
    try:
        df["Amount (₹)"] = pd.to_numeric(df["Amount (₹)"], errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"])
        weekly_data = df[df["Date"] >= pd.to_datetime(date.today()) - pd.Timedelta(days=7)]
        total_spent = weekly_data["Amount (₹)"].sum()
        remaining = st.session_state.weekly_budget - total_spent

        st.metric("Total Spent", f"₹ {total_spent:.2f}")
        st.metric("Remaining Budget", f"₹ {remaining:.2f}")

        if remaining < 0:
            st.error("❌ You have exceeded your budget!")
        elif remaining < st.session_state.weekly_budget * 0.2:
            st.warning("⚠️ Warning: Less than 20% of your budget remaining.")
        else:
            st.info("✅ You’re within your budget!")

        st.subheader("📄 All Expenses")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error processing data: {e}")
else:
    st.info("ℹ️ No expenses logged yet.")

