import pandas as pd
import numpy as np
from support_func import *
import streamlit as st

class DataManager:
    def __init__(self):
        self.original_data = None
        self.derived_data = None
        self.synthetic_data = False

  
    def load_uploaded_file(self, uploaded_file):
        
        try:
            file_name = uploaded_file.name.lower()
        
            if file_name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            if list(df.index) != list(range(len(df))):
                df = df.reset_index()
                df.rename(columns={"index": "original_index"}, inplace=True)

            self.original_data = df
            st.session_state["original_data"] = df
        except Exception as e:
            self.original_data = None
            self.derived_data = None

    @st.cache_data
    def load_synthetic_data(self):
        generator = DataGenerator()
        self.derived_data = generator.generate()
        st.session_state["derived_data"] = self.derived_data
        self.synthetic_data = True

    def generate_derived_data(self):
        df = self.original_data
        try:
            start_row = self.start_row
            end_row = self.end_row
            selected_data = df.iloc[start_row:end_row].copy()

            new_df = pd.DataFrame()
            new_df["Date"] = pd.to_datetime(selected_data[self.date_col], errors="coerce")

            if self.dep_col != self.wit_col:
                selected_data[self.dep_col] = selected_data[self.dep_col].apply(extract_numeric_value)
                selected_data[self.wit_col] = selected_data[self.wit_col].apply(extract_numeric_value)
                new_df["Deposits"] = pd.to_numeric(selected_data[self.dep_col], errors="coerce")
                new_df["Withdrawals"] = pd.to_numeric(selected_data[self.wit_col], errors="coerce")
                new_df = combine_activity(new_df, "Deposits", "Withdrawals")
            else:
                new_df["Amount"] = pd.to_numeric(
                    selected_data[self.dep_col].apply(extract_numeric_value), errors="coerce"
                ).fillna(0)

                if new_df["Amount"].ge(0).all() or new_df["Amount"].le(0).all():
                    st.warning("⚠️ The selected column contains only one direction of cash flow (all positive or all negative). Income/expense graphs may not show correctly.")

            if self.description_col:
                new_df["Description"] = selected_data[self.description_col].astype(str).fillna("Unknown")
            else:
                new_df["Description"] = "N/A"

            if self.balance_col:
                selected_data[self.balance_col] = selected_data[self.balance_col].apply(extract_numeric_value)
                balance = pd.to_numeric(selected_data[self.balance_col], errors="coerce")
                new_df["Balance"] = balance.fillna(np.nan)
            else:
                new_df["Balance"] = np.nan

            new_df = new_df.reset_index(drop=True)
            self.derived_data = new_df
            st.session_state["derived_data"] = new_df

        except Exception as e:
            st.error(f"Error generating derived data: {e}")
            self.derived_data = None
            st.session_state["derived_data"] = None
