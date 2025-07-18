import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------------------
# 1. Connect to Google Sheet
# ---------------------------
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["GOOGLE_SHEETS_CREDS"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("BudgetGuruApp").sheet1  # Make sure the sheet name is correct & shared
    return sheet

# -----------------------------
# 2. Read or Write Budget Cell
# -----------------------------
def read_budget(sheet):
    try:
        value = sheet.acell('B1').value
        return float(value) if value else 0
    except:
        return 0

def write_budget(sheet, budget_value):
    # Set headers if not already
    if sheet.acell('A1').value != "Budget":
        sheet.update('A1', 'Budget')
        sheet.update('B1', str(budget_value))
    else:
        sheet.update('B1', str(budget_value))

# ----------------------------
# 3. Read & Add Expense Logic
# ----------------------------
def add_expense_to_sheet(sheet, date, category, subcategory, amount):
    values = [str(date), category, subcategory, float(amount)]
    
    # Check if headers exist in row 3
    if sheet.acell('A3').value != 'Date':
        sheet.update('A3:D3', [["Date", "Category", "Subcategory", "Amount (₹)"]])
    
    # Append below existing expenses
    sheet.append_row(values, value_input_option="USER_ENTERED")

def get_all_expenses_from_sheet(sheet):
    data = sheet.get_all_values()
    df = pd.DataFrame(data[3:], columns=data[2])  # From Row 4 down, using Row 3 as headers
    if not df.empty:
        df["Amount (₹)"] = pd.to_numeric(df["Amount (₹)"], errors='coerce').fillna(0)
        return df
    else:
        return pd.DataFrame(columns=["Date", "Category", "Subcategory", "Amount (₹)"])

# --------------------------
# 4. Main App Interface
# --------------------------
st.set_page_config(page_title="💰 BudgetGuru App", layout="centered")
st.title("💰 BudgetGuru – Personal Expense Advisor")

sheet = connect_to_gsheet()

# Budget Input (always fetched fresh from sheet)
weekly_budget = read_budget(sheet)

with st.expander("💸 Set Weekly Budget"):
    budget_input = st.number_input("Enter your weekly budget (₹)", min_value=0, value=int(weekly_budget), step=100)
    if st.button("✅ Set Budget"):
        write_budget(sheet, budget_input)
        st.success("Weekly budget updated!")

# Category & Subcategory
subcategory_options = {
    "Food": ["Lunch", "Snacks", "Dinner", "Groceries"],
    "Shopping": ["Clothes", "Gadgets", "Accessories"],
    "Bills": ["Electricity", "Internet", "Water"],
    "Travel": ["Cab", "Bus", "Train"],
    "Other": ["Medical", "Miscellaneous"]
}

st.header("📝 Add Expense")

expense_date = st.date_input("📅 Date", value=datetime.date.today())
main_category = st.selectbox("📂 Category", list(subcategory_options.keys()))
sub_category = st.selectbox("🔻 Subcategory", subcategory_options.get(main_category, []))
amount = st.number_input("💲 Amount Spent (₹)", min_value=0)

if st.button("➕ Add Expense"):
    if amount > 0:
        add_expense_to_sheet(sheet, expense_date, main_category, sub_category, amount)
        st.success("Expense added!")
    else:
        st.warning("Please enter an amount greater than 0")

# ---------------------------
# 5. Display Weekly Summary
# ---------------------------
st.header("📊 Weekly Summary")

expenses_df = get_all_expenses_from_sheet(sheet)
total_spent = expenses_df["Amount (₹)"].sum()
remaining = weekly_budget - total_spent

col1, col2, col3 = st.columns(3)
col1.metric("💰 Weekly Budget", f"₹ {weekly_budget}")
col2.metric("💸 Total Spent", f"₹ {total_spent}")
col3.metric("✅ Remaining", f"₹ {remaining}")

# ---------------------------
# 6. Display Expense Table
# ---------------------------
st.header("📋 Expense Log")
st.dataframe(expenses_df, use_container_width=True)
