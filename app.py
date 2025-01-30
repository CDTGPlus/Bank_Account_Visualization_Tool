import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import warnings
import tempfile
import os
from support_func import *



st.set_page_config(page_title="Visual Manager", page_icon=':money_with_wings:')

#use warning to filter plotly ".to_datetime" warning
warnings.simplefilter("ignore", category=FutureWarning)

st.title("Personal Finance Manager")
st.write('Generate visual summary of account activity')
# Initialize session state for derived data
if "derived_data" not in st.session_state:
    st.session_state["derived_data"] = None
# var to alert end user if current data is randomly generated
synthetic_data = False
valid_data = False
#advanced setting
adv = False
data_source = st.sidebar.radio("Choose a data source:", ("Upload File", "Generate Random Data"))
if data_source == "Upload File":
    advanced = st.checkbox("Advanced")
    if advanced:
        st.write("""Advanced Option allows the program to read data that doesn't conform to a traditional structure.
                    Use in case of irregular rows or columns""")
        adv = True 
    else:
        adv = False
        
    # upload file
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"], key="uploaded_file")


    if uploaded_file:
        synthetic_data = False
        # error handling if file structure is not valid

        try:
                
            # set file extension to lower case
            file_name = uploaded_file.name.lower()
            # print(file_name)
            
            if adv == True:
                # if adavanced option slected, save file as temporary file for further management
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[-1]) as temp_file:
                    temp_file.write(uploaded_file.read())  # Save the uploaded file
                    temp_file_path = temp_file.name  # Get the path to the temporary file
                
                if file_name.endswith(".csv"):
                    df = dynamic_read_csv(temp_file_path)
                elif file_name.endswith(".xlsx"):
                    df = dynamic_read_excel(temp_file_path)
                # print(df)
                os.remove(temp_file_path)
            else:
                # display the uploaded file as a dataframe
                if file_name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                elif file_name.endswith(".xlsx"):
                    df = pd.read_excel(uploaded_file,engine='openpyxl')

            # reset index if index is not numerical 
            if list(df.index) != list(range(len(df))):
                df = df.reset_index()
                df.rename(columns={"index": "original_index"}, inplace=True)
            st.session_state["original_data"] = df
            st.write("### Original Data Preview")
            st.dataframe(df, use_container_width=True)
        

            # Column selection and range inputs below the original data
            st.subheader("Assign Columns and Select Data Range")
            date_col = st.selectbox("Select Date Column (Required)", df.columns, key="date")
            # for Amount column, make selection if Deposits and Withdraws are a single column or multiple
            st.warning("""Note: If Deposits and Withdrawals are in a single column,
                        select the same column for both parameters""")
            dep_col = st.selectbox("Select Deposit Column (Required)", df.columns, key="deposit")
            wit_col = st.selectbox("Select Withdrawal Column (Required)", df.columns, key="withdrawal")
            description_col = st.selectbox("Select Description Column (Optional)", [None] + list(df.columns), key="description")
            balance_col = st.selectbox("Select Balance Column (Optional)", [None] + list(df.columns), key="balance")

            # range selection for rows
            st.write("### Select Data Range")
            start_row = st.number_input("Start Row", min_value=0, max_value=len(df) - 1, value=0, step=1, key="start_row")
            end_row = st.number_input("End Row", min_value=0, max_value=len(df), value=len(df), step=1, key="end_row")

        

            # Button to confirm assigned columns and range selection
            if st.button("Generate Derived Data"):
                
                # Validate required columns and range
                if not date_col or not dep_col or not wit_col:
                    st.error("Date and Amount columns are required.")
                elif start_row >= end_row:
                    st.error("Start Row must be less than End Row.")
                else:
                    # Create a new dataframe with selected columns and range
                    selected_data = df.iloc[start_row:end_row]
                    
                    try:
                        new_df = pd.DataFrame()
                        new_df["Date"] = pd.to_datetime(selected_data[date_col], errors="coerce")
                        
                        # Check for invalid dates
                        if new_df["Date"].isna().any():
                            raise ValueError("Invalid dates detected in the selected Date column.")
                        
                        if dep_col != wit_col:
                            selected_data[dep_col] = selected_data[dep_col].apply(extract_numeric_value)
                            selected_data[wit_col] = selected_data[wit_col].apply(extract_numeric_value)
                            new_df["Deposits"] = pd.to_numeric(selected_data[dep_col], errors="coerce")
                            new_df["Withdrawals"] = pd.to_numeric(selected_data[wit_col], errors="coerce")
                            new_df = combine_activity(new_df,"Deposits","Withdrawals")
                        else:
                            new_df["Amount"] = pd.to_numeric(selected_data[dep_col], errors="coerce")
                            new_df["Amount"] = new_df["Amount"].fillna(0)
                        
                        
                        # Check for invalid amounts
                        if new_df["Amount"].isna().any():
                            raise ValueError("Invalid numeric values detected in the selected Amount column.")
                        
                        if description_col:
                            if not pd.api.types.is_object_dtype(selected_data[description_col]):
                                raise ValueError("Description column must contain text data.")
                            new_df["Description"] = selected_data[description_col].astype(str)
                        else:
                            new_df["Description"] = "N/A"
                        
                        if balance_col:
                            # print(selected_data[balance_col].dtype)
                            # print(selected_data[balance_col])
                            selected_data[balance_col] = selected_data[balance_col].apply(extract_numeric_value)
                            # print('Alert: ',selected_data[balance_col].dtype)
                            new_df["Balance"] = pd.to_numeric(selected_data[balance_col], errors="coerce")
                            # Check for invalid balances
                            new_df["Balance"] = new_df['Balance'].fillna(0)
                        else:
                            new_df["Balance"] = np.nan
                        
                        # Reset index of the derived dataframe
                        new_df = new_df.reset_index(drop=True)
                        new_df.reset_index(drop=True,inplace=True)
                        # Save derived data to session state
                        st.session_state["derived_data"] = new_df
                        
                    except ValueError as e:
                    # Display the error to the user
                        st.error(f"Error: {str(e)}")
                    
        except Exception as e:
            st.write('Uploaded Data not valid.')
            st.write('Try Using Advanced Settings. User Might have to Use Custom Range')

    else:
        # clear session state when no file is uploaded
        st.session_state.pop("original_data", None)
        st.session_state.pop("derived_data", None)

else:
    # if user chooses, system generated data, generate demo data using support class
    data = DataGenerator()
    new_df = data.generate()
    st.session_state["derived_data"] = new_df
    synthetic_data = True

if "derived_data" in st.session_state and st.session_state["derived_data"] is not None:
    try:
        new_df = st.session_state["derived_data"]
        min_date = new_df["Date"].min().date()
        max_date = new_df["Date"].max().date()
        st.subheader("Filter Data by Date Range")
        selected_date_range = st.date_input(
            "Select Date Range", 
            [min_date, max_date],  # Default range
            min_value=min_date, 
            max_value=max_date)
        
        if len(selected_date_range) == 2:
            selected_start_date, selected_end_date = selected_date_range
        # Ensure start_date is before end_date
        if selected_start_date > selected_end_date:
            st.error("Start date cannot be after end date. Please adjust your selection.")
        else:
            # Filter the dataframe based on selected date range
            new_df = new_df[
                (new_df["Date"].dt.date >= selected_start_date) & 
                (new_df["Date"].dt.date <= selected_end_date)
            ]

        if synthetic_data == True:
            st.warning('Current Data in use has been generated by program.')

        st.subheader("Derived Data (Transformed View)")
        st.dataframe(new_df, use_container_width=True)

        # check if required columns exist in the derived dataframe
        if "Date" not in new_df.columns or "Amount" not in new_df.columns:
            st.error("The derived data is missing required columns: 'Date' and 'Amount'.")
        else:
            # Graph for account activity, can be yearly, monthlly or dialy basis, generate respective columns
            st.subheader("Account Activity Over Time")
            time_period = st.radio("Select Timeframe", ("Total","Yearly", "Monthly", "Daily"))

            if time_period == "Total":
                fig =px.line(new_df, x= new_df["Date"], y = new_df["Amount"], title = "Complete Account Activity")
                st.plotly_chart(fig)
            elif time_period == "Yearly":
                if new_df["Date"].isnull().all():
                    st.warning("Cannot group by Year. The 'Date' column contains invalid or missing dates.")
                else:
                    new_df["Year"] = new_df["Date"].dt.year
                    activity = new_df.groupby("Year")["Amount"].sum()
                    fig = px.line(activity, x=activity.index, y="Amount", title="Yearly Account Activity")
                    st.plotly_chart(fig)
            elif time_period == "Monthly":
                if new_df["Date"].isnull().all():
                    st.warning("Cannot group by Month. The 'Date' column contains invalid or missing dates.")
                else:
                    new_df["Month"] = new_df["Date"].dt.to_period("M")
                    activity = new_df.groupby("Month")["Amount"].sum()
                    fig = px.line(activity, x=activity.index.astype(str), y="Amount", title="Monthly Account Activity")
                    st.plotly_chart(fig)
            else:
                if new_df["Date"].isnull().all():
                    st.warning("Cannot group by Day. The 'Date' column contains invalid or missing dates.")
                else:
                    new_df["Day"] = new_df["Date"].dt.date
                    activity = new_df.groupby("Day")["Amount"].sum()
                    fig = px.line(activity, x=activity.index, y="Amount", title="Daily Account Activity")
                    st.plotly_chart(fig)

            if len(new_df["Description"]) > 0:
                st.subheader("Income and Expenses by Description")
                try:
                    new_df["Type"] = np.where(new_df["Amount"] >= 0, "Income", "Expense")
                    grouped = new_df.groupby(["Type", "Description"])["Amount"].sum().reset_index()
                    
                    for t in ["Income", "Expense"]:
                        st.write(f"### {t}")
                        filtered = grouped[grouped["Type"] == t]
                        if filtered.empty:
                            st.warning(f"No {t.lower()} data available.")
                        else:
                            fig = px.bar(filtered, x="Description", y="Amount", title=f"{t} by Description")
                            st.plotly_chart(fig)
                            st.write(f"Total {t}: {filtered['Amount'].sum():,.2f}")
                except Exception as e:
                    st.error(f"Error processing income and expenses by description: {str(e)}")
            else:
                st.warning("The selected description column is missing or invalid.")

            # Balance graph
            if len(new_df["Balance"]) > 0:
                st.subheader("Balance Over Time")
                try:
                    balance_data = new_df.sort_values(by="Date")[["Date", "Balance"]].dropna()
                    if balance_data.empty:
                        st.warning("No valid data available for balance plotting.")
                    else:
                        fig = px.line(balance_data, x="Date", y="Balance", title="Balance Over Time")
                        st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"Error generating balance graph: {str(e)}")
            else:
                st.info("Balance column not selected or contains no valid data.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
else:
    st.info("No derived data available. Please upload a file and generate derived data.")
