import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="💰 BudgetGuru", layout="centered")

st.title("💰 BudgetGuru – Personal Expense Tracker")

# Initialize session state
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Category", "Amount (₹)"])

if "weeklybudget" not in st.session_state:
    st.session_state.weeklybudget = 0

# -----------------------------------------------
st.subheader("1️⃣ Set Weekly Budget")

budget_input = st.number_input("Enter your weekly budget (₹):", min_value=0, step=100)
if st.button("✅ Set Weekly Budget"):
    st.session_state.weeklybudget = budget_input
    st.success(f"Weekly budget set to ₹{budget_input}")

# -----------------------------------------------
st.subheader("2️⃣ Add Daily Expense")

expense_date = st.date_input("🗓️ Date", value=date.today())
category = st.selectbox("📂 Category", ["Groceries", "Transport", "Entertainment", "Dining", "Utilities", "Misc"])
amount = st.number_input("💸 Amount spent (₹):", min_value=0, step=10)

if st.button("➕ Add Expense"):
    new_expense = {"Date": str(expense_date), "Category": category, "Amount (₹)": amount}
    st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_expense])], ignore_index=True)
    st.success("✅ Expense added!")

# -----------------------------------------------
st.subheader("3️⃣ Weekly Summary")

total_spent = st.session_state.expenses["Amount (₹)"].sum()
remaining = st.session_state.weeklybudget - total_spent

st.info(f"💵 Total Spent: ₹{total_spent}")
st.info(f"🧮 Remaining Budget: ₹{remaining}")

# Tips
if remaining <= 0:
    st.error("🚨 You’ve exceeded your weekly budget! Consider cutting back on extras.")
elif remaining < st.session_state.weeklybudget * 0.2:
    st.warning("⚠️ Only 20% of your budget remains. Be cautious!")
else:
    st.success("✅ You’re managing your budget well! Keep it up!")

# -----------------------------------------------
st.subheader("📊 All Expenses")
st.dataframe(st.session_state.expenses, use_container_width=True)
