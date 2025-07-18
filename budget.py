import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------- 1. Connect to Google Sheet -------------------- #
def connect_to_gsheet():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = st.secrets["GOOGLE_SHEETS_CREDS"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        sheet = client.open("BudgetGuruApp").sheet1  # Sheet name must match exactly
        return sheet
    except Exception as e:
        st.error("❌ Failed to connect to Google Sheet. Make sure you've shared the sheet with the service account.")
        st.stop()

# -------------------- 2. Initialize Sheet Headers (if empty) -------------------- #
def ensure_headers(sheet):
    try:
        headers = sheet.row_values(1)
        if not headers or headers != ['Date', 'Main Category', 'Subcategory', 'Amount (₹)']:
            sheet.update('A1:D1', [['Date', 'Main Category', 'Subcategory', 'Amount (₹)']])
    except Exception as e:
        st.error("❌ Failed to ensure headers in the sheet.")
        st.stop()

# -------------------- 3. Save budget to sheet -------------------- #
def write_budget(sheet, budget):
    try:
        sheet.update('F1', 'Weekly Budget')
        sheet.update('F2', str(budget))
    except:
        st.warning("⚠️ Could not save weekly budget. Budget will reset on refresh.")

# -------------------- 4. Load budget from sheet -------------------- #
def read_budget(sheet):
    try:
        return int(sheet.acell('F2').value)
    except:
        return 0

# -------------------- 5. Save expense -------------------- #
def add_expense_to_sheet(sheet, date, main_cat, sub_cat, amount):
    sheet.append_row([str(date), main_cat, sub_cat, amount])

# -------------------- 6. UI Starts -------------------- #
st.set_page_config(page_title="BudgetGuru 💰", layout="centered")
st.title("📊 BudgetGuru – Smart Weekly Expense Tracker")

sheet = connect_to_gsheet()
ensure_headers(sheet)

# -------------------- Budget Section -------------------- #
weekly_budget = read_budget(sheet)

if weekly_budget == 0:
    budget_input = st.number_input("Set your weekly budget (₹):", min_value=100, step=100)
    if st.button("Set Budget"):
        write_budget(sheet, budget_input)
        weekly_budget = budget_input
        st.success("✅ Budget saved successfully!")
else:
    st.success(f"✅ Weekly Budget: ₹{weekly_budget}")

st.divider()

# -------------------- Expense Entry Section -------------------- #
st.subheader("➕ Add Expense")

expense_date = st.date_input("🗓️ Date", value=datetime.date.today())

main_category = st.selectbox("Main Category", [
    "Food", "Bills", "Shopping", "Entertainment", "Transport", "Health", "Other"
])

subcategory_options = {
    "Food": ["Breakfast", "Lunch", "Dinner", "Snacks", "Other"],
    "Bills": ["Electricity", "Internet", "Gas", "Water", "Other"],
    "Shopping": ["Clothes", "Electronics", "Groceries", "Other"],
    "Entertainment": ["Movies", "Games", "Subscription", "Other"],
    "Transport": ["Bus", "Train", "Fuel", "Taxi", "Other"],
    "Health": ["Medicine", "Doctor Visit", "Insurance", "Other"],
    "Other": ["Miscellaneous"]
}

sub_category = st.selectbox("Subcategory", subcategory_options[main_category])
amount = st.number_input("💸 Amount Spent (₹):", min_value=1, step=1)

if st.button("Add Expense"):
    add_expense_to_sheet(sheet, expense_date, main_category, sub_category, amount)
    st.success("✅ Expense added!")

# -------------------- Expense Table -------------------- #
st.divider()
st.subheader("📅 Weekly Summary")

data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    total_spent = df["Amount (₹)"].sum()
    remaining = weekly_budget - total_spent
    st.metric("Total Spent", f"₹{total_spent}")
    st.metric("Remaining", f"₹{remaining}")
    st.dataframe(df[::-1], use_container_width=True)
else:
    st.info("No expenses added yet.")

