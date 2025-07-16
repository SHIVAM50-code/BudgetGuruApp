
import streamlit as st
import pandas as pd
import gspread
import json
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials

# Function to connect to Google Sheets

def connect_to_gsheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    try:
        sheet = client.open("BudgetGuruApp").sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ Could not open the sheet. Reason: {e}")
        st.stop()


# Function to add expense to sheet
def add_expense_to_sheet(sheet, date, category, amount):
    sheet.append_row([str(date), category, amount])

# Streamlit App
st.set_page_config(page_title="BudgetBuddy 💰", page_icon="💸")
st.title("💰 BudgetBuddy – Your Personal Expense Tracker")

# Connect to Google Sheet
sheet = connect_to_gsheet()

# Weekly budget input with session state
if "weekly_budget" not in st.session_state:
    st.session_state.weekly_budget = 0

if st.session_state.weekly_budget == 0:
    input_budget = st.number_input("💰 Enter your weekly budget (in ₹)", min_value=0, step=100, key="budget_input")
    if st.button("✅ Set Budget"):
        st.session_state.weekly_budget = input_budget
        st.success(f"Weekly budget set to ₹{input_budget}")
else:
    st.info(f"📌 Your weekly budget is: ₹{st.session_state.weekly_budget}")
    if st.button("🔄 Reset Budget"):
        st.session_state.weekly_budget = 0

# Initialize expenses DataFrame in session state
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Category", "Amount (₹)"])

# Expense form
st.header("➕ Log a New Expense")

with st.form("expense_form"):
    expense_date = st.date_input("🗓️ Date", value=date.today())
    category = st.selectbox("📁 Category", ["Food", "Rent", "Transport", "Entertainment", "Others"])
    amount = st.number_input("💸 Amount (in ₹)", min_value=0, step=1)
    submit = st.form_submit_button("Add Expense")

if submit:
    new_expense = {"Date": expense_date, "Category": category, "Amount (₹)": amount}
    add_expense_to_sheet(sheet, expense_date, category, amount)
    st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_expense])], ignore_index=True)
    st.success("✅ Expense added successfully!")

# Show expense history
st.header("📜 Expense History")
st.dataframe(st.session_state.expenses, use_container_width=True)

# Summary
total_spent = st.session_state.expenses["Amount (₹)"].sum()
remaining = st.session_state.weekly_budget - total_spent

st.subheader("📊 Weekly Summary")
st.info(f"Total Spent: ₹{total_spent}")
st.success(f"Remaining Budget: ₹{remaining}")

if remaining < 0:
    st.error("⚠️ You overspent your weekly budget!")
elif remaining < st.session_state.weekly_budget * 0.2:
    st.warning("💡 You're nearing your budget limit.")
else:
    st.balloons()
    st.success("🎉 You're managing your budget well!")
