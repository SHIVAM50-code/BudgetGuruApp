import streamlit as st
import pandas as pd
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_gsheet():
    scope =['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name('budgetguru-credentials.json',scope)
    client = gspread.authorize(creds)

    sheet = client.open("BudgetGuruApp").sheet1
    return sheet

def add_exense_to_sheet(sheet,date,category,amount):
    sheet.append_row([str(date),category,amount])


st.set_page_config(page_title="BudgetGuru 💰",page_icon= "💸")
st.title("💰 BudgetGuru 💰 - Your expenses Tracker ")
st.markdown("Track your daily expenses and get smart saving tips!!!")

sheet = connect_to_gsheet()




if "weekly_budget" not in st.session_state:
    st.session_state.weekly_budget= 0

if st.session_state.weekly_budget==0:
    st.session_state.weekly_budget = st.number_input("Whats your weekly budget?(in ,₹)",min_value=0,step=100, key="budget_input")
    if st.button("✅ Set Budget"):
        st.session_state.weeklybudget = weekly_budget # type: ignore
        st.success(f"Weekly budget set to ₹{weekly_budget}") # type: ignore

st.success(f"Weekly Budget:₹{st.session_state.weekly_budget}")


if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date","Category","Amount(₹)"])

st.header(" ➕Log New Expense")

with st.form ("expense_form"):
    expense_date= st.date_input(" 🗓️ Date",value=date.today())
    category =st.selectbox("📁 Category",["Food","Stationary","Petrol","HouseHold","Other"])
    amount=st.number_input("💸 Amount(₹)",min_value=0,step=1)
    submit=st.form_submit_button("Add Expense")

if submit:
    new_expense ={"Date":expense_date,"Category":category,"Amount(₹)":amount}
    add_expense_to_sheet(sheet, expense_date, category, amount) # type: ignore
    st.session_state.expenses =pd.concat([st.session_state.expenses,pd.DataFrame([new_expense])],ignore_index=True)
    st.success("Expense added sucessfully!")

st.header("📜 Expense History")
st.dataframe(st.session_state.expenses,use_container_width=True)

total_spent = st.session_state.expenses["Amount(₹)"].sum()
remaining = st.session_state.weekly_budget - total_spent

st.subheader("📊 Weekly Summary")
st.info(f"Total Spent : ₹{total_spent}")
st.success(f"Remaining Budget : ₹{remaining}")

if remaining<0:
    st.error("⚠️ You overspent your weekly budget!")
elif remaining < st.session_state.weekly_budget*0.2:
    st.warning("💡 You are nearing your budget limit.")
else:
    st.balloons()
    st.success( "You are managing your budget well..")





