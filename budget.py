'''
title: Budget App
author: Hannah Wasson
description: This Streamlit app helps track expenses and calculate savings based on my paycheck. 
It allows you to allocate funds across categories, visualize spending with a pie chart, and set savings goals
while ensuring you stay within budget.
'''

# Importing necessary packages
import streamlit as st
import numpy as np 
import pandas as pd
import os
import plotly.express as px
from datetime import date

# CSV files used throughout 
b = 'budget.csv' # you will need to make sure these are in your directory! 
e = 'expenses.csv' # you will need to make sure these are in your directory! 

# functions used throughout app
def create_dataframe(csv): 
    df = pd.read_csv(csv)
    return df

def time_plot(data, cat):
    group = data.groupby(['Month', 'Category'])['Amount'].sum().reset_index()
    filtered = group[group['Category'] == cat]
    filtered = filtered.sort_values(by = 'Month')
    fig = px.line(filtered, x='Month', y='Amount', title=f"Change in {cat} Over Time", color_discrete_sequence = ['black'])
    st.plotly_chart(fig)

def pie_chart(data, group): 
    fig = px.pie(data, values=group, names='Category', color_discrete_sequence=px.colors.sequential.Greens)
    st.plotly_chart(fig)

def bar_chart(data_csv): 
    data = pd.read_csv(data_csv)
    df_melted = pd.melt(data, id_vars=['Month'], var_name='Account Type', value_name='Amount')
    df_melted = df_melted.sort_values(by='Month')
    df_melted = df_melted[df_melted['Account Type'].isin(['saving1', 'saving2', 'saving3', 'Total Saved'])]
    df_melted_g = df_melted.groupby('Account Type')['Amount'].sum().reset_index()
    fig = px.bar(df_melted_g, x='Account Type', y='Amount', color = 'Account Type', color_discrete_sequence=px.colors.sequential.Greens)
    st.plotly_chart(fig)

def check_budget_exists(budget_csv = b): 
        # Load existing data if the file exists
    if os.path.exists(budget_csv):
        try:
            budget_df = create_dataframe(budget_csv)
        except Exception as error:
            st.error(f"Error reading CSV: {error}")
            budget_df = pd.DataFrame(columns=["Month", "Paycheck", "saving1", "saving2", "STS", "Total_Saved", "Fixed_Expenses", "Misc_Budget"])
    else:
        budget_df = pd.DataFrame(columns=["Month", "Paycheck", "saving1", "saving2", "STS", "Total_Saved", "Fixed_Expenses", "Misc_Budget"])

    return budget_df

def check_expense_exists(expense_csv = e): 
    if os.path.exists(expense_csv):
        try:
            expense_df = create_dataframe(expense_csv)
        except Exception as error:
            st.error(f"Error reading CSV: {error}")
            expense_df = pd.DataFrame(columns=["Month", "Amount", "Category", "Planned_Unplanned", "Description"])
    else:
        expense_df = pd.DataFrame(columns=["Month", "Amount", "Category", "Planned_Unplanned", "Description"])

    return expense_df

# SETTING UP STREAMLIT APP
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_icon="💵", page_title="Personal Finance Hub")

# Sidebar Navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Finances at a Glance", "Allocate my Paycheck", "Log my Expenses", "Historical Data"], 
    index=0
)

# PAGE: Finances at a Glance
if page == "Finances at a Glance": 
    st.title("Finances at a Glance")

    try: 
        finances_df = create_dataframe(e)
        finances_df = finances_df.sort_values(by = 'Month') # Select only numeric columns
        grouped_finances = finances_df.groupby(['Month', 'Category'])['Amount'].sum().reset_index() # Compute percentage change
        grouped_finances['Amount_PctChange'] = grouped_finances.groupby(['Month', 'Category'])['Amount'].pct_change().fillna(0)

        st.header("Change in Expense Category by Month")
        c1, c2, c3 = st.columns(3)
    
        with c1:
            time_plot(finances_df,'Rent')
            mean_rent = grouped_finances[grouped_finances['Category'] == 'Rent']['Amount_PctChange'].mean()
            if not mean_rent: 
                st.metric("Average Percent Change in Rent Over Time", f"{round(mean_rent, 2) * 100}%")
        with c2:
            time_plot(finances_df,'Utilities')
            mean_utilities = grouped_finances[grouped_finances['Category'] == 'Rent']['Amount_PctChange'].mean()
            if not mean_utilities:    
                st.metric("Average Percent Change in Utilities Over Time", f"{round(mean_utilities, 2) * 100}%")
        with c3:
            time_plot(finances_df,'Groceries')
            mean_groceries = grouped_finances[grouped_finances['Category'] == 'Rent']['Amount_PctChange'].mean()
            if not mean_groceries: 
                st.metric("Average Percent Change in Rent Over Time", f"{round(mean_groceries, 2) * 100}%")
        
        st.divider()

        st.header("Proportion of Total Expenses by Month and Category")
        month_select = st.selectbox("Select Month", grouped_finances['Month'].unique())
        
        try: 
            pie_chart(grouped_finances[grouped_finances['Month'] == month_select], 'Amount')
            st.metric("Sum of Expenses by Month ($)", round(grouped_finances[grouped_finances['Month'] == month_select]['Amount'].sum(), 2))
        except: 
            st.write("There are no logged expenses.")

        st.divider()
        st.header("Savings by Account Type")

        try: 
            bar_chart(b)
        except: 
            st.write('There are no logged savings.')

    except FileNotFoundError:
        st.error("Error: budget.csv not found. Please upload or create a budget file.")
    except Exception as e:
        st.error(f"Error: {e}")

# PAGE: Allocate my Paycheck
if page == "Allocate my Paycheck": 
    st.header("Allocate my Paycheck")

    budget_df = check_budget_exists()

    with st.form("paycheck_form"): 

        # Customizable inputs for contribution percentages
        saving1 = st.slider("Select contribution percentage to Savings Fund 1", min_value=0.0, max_value=0.30, value=0.2)
        saving2 = st.slider("Select contribution percentage to Savings Fund 2", min_value=0.0, max_value=0.30, value=0.15)
        saving3 = st.slider("Select contribution percentage to Savings Fund 3", min_value=0.0, max_value=0.30, value=0.10)

        # Date input and converting it to month/year format 
        curr_date = st.date_input("What's the date?", value=None, format="MM/DD/YYYY")
        if curr_date:
            month = curr_date.strftime("%m/%Y")
        
        paycheck = st.number_input("Input take-home paycheck amount...", min_value=0.0)
        
        try:
            expense_df = check_expense_exists()
            rent_max = expense_df[expense_df['Category'] == 'Rent']['Amount'].max() if not expense_df[expense_df['Category'] == 'Rent'].empty else 0
            subscriptions_max = expense_df[expense_df['Category'] == 'Subscriptions']['Amount'].max() if not expense_df[expense_df['Category'] == 'Subscriptions'].empty else 0
            groceries_avg = expense_df[expense_df['Category'] == 'Groceries']['Amount'].mean() if not expense_df[expense_df['Category'] == 'Groceries'].empty else 0
            utilities_max = expense_df[expense_df['Category'] == 'Utilities']['Amount'].max() if not expense_df[expense_df['Category'] == 'Utilities'].empty else 0
            gas_max = expense_df[expense_df['Category'] == 'Gas']['Amount'].mean() if not expense_df[expense_df['Category'] == 'Gas'].empty else 0
            pet_avg = expense_df[expense_df['Category'] == 'Pet Expenses']['Amount'].mean() if not expense_df[expense_df['Category'] == 'Pet Expenses'].empty else 0
            gym_max = expense_df[expense_df['Category'] == 'Gym Membership']['Amount'].max() if not expense_df[expense_df['Category'] == 'Gym Membership'].empty else 0

        except FileNotFoundError:
            st.error("Expenses file not found.")
            rent_max = subscriptions_max = groceries_avg = utilities_max = gas_max = pet_avg = 0

        # Calculating the portion of paycheck going to each fund and adding them to total saved
        saving1_acct = paycheck * saving1
        saving2_acct = paycheck * saving2
        saving3_acct = paycheck * saving3
        total_saved = saving1_acct + saving2_acct + saving3_acct

        # Calculating fixed & miscellaneous budgets
        fixed_budget = rent_max + subscriptions_max + groceries_avg + utilities_max + gas_max + pet_avg
        misc_budget = paycheck - (total_saved + fixed_budget)

        st.divider()
        
        # Button to log the paycheck
        submitted = st.form_submit_button("Submit Paycheck")
        # If the paycheck is submitted, append a new row to the budget dataframe
        if submitted:
            # Append new data
            new_data = pd.DataFrame([[month, paycheck, saving1_acct, saving2_acct, sts_acct, total_saved, fixed_budget, misc_budget]], columns=budget_df.columns)
            budget_df = pd.concat([budget_df, new_data], ignore_index=True)
            budget_df.to_csv(b, index=False)
            st.success("Your paycheck has been successfully allocated!")
            st.balloons()

    
    # Showing the expense summary of how much of the paycheck was allocated to each fund
    st.header("Expense Summary")
    st.subheader("Savings Allocation")

    a, b, c, d = st.columns(4)
    with a: 
        st.metric("Savings Fund 1 ($):", round(saving1_acct, 2))
    with b: 
        st.metric("Savings Fund 2 ($):", round(saving2_acct, 2))
    with c: 
        st.metric("Savings Fund 3 ($):", round(saving3_acct, 2))
    with d: 
        st.metric("Total Saved ($):", round(total_saved, 2))

    st.divider()

    # Showing the total amount from the paycheck allocated to fixed expenses - dynamically adjusting for new expenses
    st.subheader("Fixed Expenses")
    st.metric("Total Allocation to Fixed Expenses ($):", f"${round(fixed_budget, 2):,.2f}")

    st.divider()

    # Showing the total amount from the paycheck allocated to discretionary expenses -- 
    # anything that is left over after savings and fixed expenses are taken out
    st.subheader("Discretionary Spend")
    st.metric("Total Left to Spend", f"${round(misc_budget, 2):,.2f}")

# PAGE: Log my Expenses
if page == "Log my Expenses": 
    st.title("Log my Expenses")
        
    e_df = check_expense_exists()
    b_df = check_budget_exists()

    with st.form("expense_form"): 
        st.subheader("Expense Form")
        curr_date = st.date_input("What's the date?", value = None, format = "MM/DD/YYYY")
        if curr_date: month = curr_date.strftime("%m/%Y")
        amount = st.number_input("How much did you spend?")
        category = st.selectbox(
            "What category does this fall into?",
            ("Rent", "Utilities", "Car Insurance", "Gas", "Public Transportation", 
            "Groceries", "Dining Out", "Delivery Services", "Renters Insurance", 
            "Medical Expenses", "Gym Membership", "Health-Related Products", 
            "Subscriptions", "Movies, Concerts, Events", "Hobbies", "Travel",
            "Haircut", "Skincare, Makeup", "Clothes", "Toiletries (soap, toothpaste, etc.)", 
            "Gifts", "Pet Expenses", "Other")
        )
        scheduled = st.pills("Was this expense planned?", ['Yes', 'No'])
        description = st.text_input("What was this expense?")

        expense_submit = st.form_submit_button("Log Expense")

        if expense_submit:
            # Append new expense to the expense dataframe
            new_data = pd.DataFrame([[month, amount, category, scheduled, description]], columns=e_df.columns)
            e_df = pd.concat([e_df, new_data], ignore_index=True)
            e_df.to_csv(e, index=False)
            st.success("Your expense has been successfully logged!")
            st.balloons()

    # This is now getting into giving the current expense summary
    st.header('Expense Summary')

    expense_summary = check_expense_exists()
    budget_check = check_budget_exists()

    select_month = st.selectbox("Select which month you want to see expenses for..." , options=expense_summary['Month'].unique())

    try:
        st.subheader('Miscellaneous Expenses')
        month_misc_expenses = expense_summary.groupby(['Month', 'Category'])['Amount'].sum()
        st.dataframe(month_misc_expenses[select_month], use_container_width=True)
        total_misc_expenses = month_misc_expenses[select_month].sum()
        st.metric('Total Miscellaneous Expenses (Month)', f"${round(total_misc_expenses, 2):,.2f}")
        
        misc = budget_check[budget_check['Month'] == select_month]['Misc_Budget'][0]
        over_by_misc = total_misc_expenses - misc
        if total_misc_expenses > misc: 
            st.warning(f"FYI you are over the miscellaneous spend budget by ${round(over_by_misc,2)}")
        else : 
            st.write("You are within the miscellaneous spend budget.")   
    except: 
        st.write("There are no miscellaneous expenses logged.")
        
    st.divider()

    st.subheader('Fixed Expenses')

    fixed_categories = ['Rent', 'Subscriptions', 'Groceries', 'Utilities', 'Gas', 'Pet Expenses', 'Gym Membership']
    month_fixed_expenses = expense_summary.groupby(['Month', 'Category'])['Amount'].sum()
    month_fixed_expenses = month_fixed_expenses[month_fixed_expenses.index.get_level_values('Category').isin(fixed_categories)]

    try:
        total_fixed_expenses = month_fixed_expenses[select_month].sum()
        st.dataframe(month_fixed_expenses[select_month], use_container_width=True)
        st.metric('Total Fixed Expenses (Month)', f"${round(total_fixed_expenses, 2):,.2f}")

        fixed = budget_check[budget_check['Month'] == select_month]['Fixed_Expenses'].iloc[0]
        over_by_fixed = total_fixed_expenses - fixed

        if total_fixed_expenses > fixed:
            st.warning(f"FYI you are over the fixed expenses budget by ${over_by_fixed:,.2f}")
        else:
            st.write("You are within the fixed expenses budget.")

    except KeyError:
        st.write('There are no fixed expenses logged.')

if page == 'Historical Data': 
    st.title('Historical Data')
    st.header('Budget History')
    b_history = create_dataframe(b).sort_values(by = 'Month')
    st.dataframe(b_history, use_container_width=True)

    st.header('Expense History')
    e_history = create_dataframe(e).sort_values(by='Month')
    st.dataframe(e_history, use_container_width=True)
