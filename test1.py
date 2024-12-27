import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Set page config
st.set_page_config(page_title="Options Position Manager", layout="wide")
st.title("Options Position Manager")

# Initialize session state for storing transactions
if 'transactions' not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=['Date', 'Action', 'Type', 'Underlying', 'Qty', 'ExpDate', 
                'Strike', 'Price', 'Commission']
    )

# Input form for new transactions
with st.form("transaction_form"):
    st.subheader("New Transaction")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date = st.date_input("Date", datetime.today())
        action = st.selectbox("Action", ["Buy", "Sell"])
        option_type = st.selectbox("Type", ["Call", "Put"])
    
    with col2:
        underlying = st.text_input("Underlying Symbol").upper()
        qty = st.number_input("Quantity", min_value=1)
        exp_date = st.date_input("Expiration Date", 
                               min_value=datetime.today())
    
    with col3:
        strike = st.number_input("Strike Price", min_value=0.0, step=0.5)
        price = st.number_input("Option Price", min_value=0.0, step=0.01)
        commission = st.number_input("Commission", value=0.0, step=0.01)

    submitted = st.form_submit_button("Add Transaction")
    
    if submitted:
        # Adjust quantity based on action (negative for sells)
        adjusted_qty = qty if action == "Buy" else -qty
        
        # Add new transaction
        new_transaction = pd.DataFrame([{
            'Date': date,
            'Action': action,
            'Type': option_type,
            'Underlying': underlying,
            'Qty': adjusted_qty,
            'ExpDate': exp_date,
            'Strike': strike,
            'Price': price,
            'Commission': commission
        }])
        
        st.session_state.transactions = pd.concat(
            [st.session_state.transactions, new_transaction], 
            ignore_index=True
        )

# Calculate positions
if not st.session_state.transactions.empty:
    positions = (st.session_state.transactions
                .groupby(['Underlying', 'Type', 'Strike', 'ExpDate'])
                .agg({
                    'Qty': 'sum',
                    'Price': lambda x: np.average(
                        x, 
                        weights=abs(st.session_state.transactions.loc[x.index, 'Qty'])
                    )
                })
                .reset_index())
    
    # Calculate days to expiration
    positions['DaysToExp'] = (
        pd.to_datetime(positions['ExpDate']) - pd.Timestamp.today()
    ).dt.days
    
    # Add mock market prices (in real app, these would come from an API)
    positions['CurrentPrice'] = positions['Price'] * 1.1  # Mock price
    
    # Calculate P/L
    positions['P/L_Open'] = (
        (positions['CurrentPrice'] - positions['Price']) * 
        positions['Qty'] * 100  # Multiply by 100 as each contract is for 100 shares
    )

# Display positions
st.subheader("Positions")
if not st.session_state.transactions.empty:
    # Add filters
    col1, col2 = st.columns(2)
    with col1:
        symbol_filter = st.multiselect(
            "Filter by Symbol",
            options=positions['Underlying'].unique()
        )
    with col2:
        type_filter = st.multiselect(
            "Filter by Option Type",
            options=positions['Type'].unique()
        )
    
    # Apply filters
    filtered_positions = positions.copy()
    if symbol_filter:
        filtered_positions = filtered_positions[
            filtered_positions['Underlying'].isin(symbol_filter)
        ]
    if type_filter:
        filtered_positions = filtered_positions[
            filtered_positions['Type'].isin(type_filter)
        ]
    
    # Display positions table
    st.dataframe(
        filtered_positions.style.format({
            'Price': '${:.2f}',
            'CurrentPrice': '${:.2f}',
            'P/L_Open': '${:.2f}'
        })
    )

# Display transactions
st.subheader("Transactions")
if not st.session_state.transactions.empty:
    st.dataframe(st.session_state.transactions)
    
    if st.button("Clear All Transactions"):
        st.session_state.transactions = pd.DataFrame(
            columns=['Date', 'Action', 'Type', 'Underlying', 'Qty', 'ExpDate', 
                    'Strike', 'Price', 'Commission']
        )
        st.experimental_rerun()
