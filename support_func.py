import re
import pandas as pd
import numpy as np
import random


from datetime import datetime, timedelta

def extract_numeric_value(value):
    var = str(type(value))
    if 'float' in var or 'int' in var:
        return float(value)
        
    # regex to find numerical value
    value = value.replace(',', '')
    match = re.search(r"[-+]?\d*\.\d+|\d+", value)
    if match:
        return float(match.group(0)) 
    else:
        return None  


# Function to ensure a numerical value is negative
def make_negative(x):
    if pd.isna(x):  # Ignore NaN values
        return x
    return -abs(x)  # Ensure the value is negative

# In case of negative, invert to positive
def invert(x):
    if x < 0:
        return abs(x)
    else:
        return x
# Function to combine Deposits and Withdrawals into a singlecolumn
def combine_activity(df, deposits_col, withdrawals_col):
    # Apply make_negative to ensure withdrawals are negative
    # df[withdrawals_col] = df[withdrawals_col].apply(make_negative)
    df[deposits_col] = df[deposits_col].fillna(0)
    df[withdrawals_col] = df[withdrawals_col].apply(invert).fillna(0)
    # create the 'activity' column by combining the Deposits and Withdrawals
    df['Amount'] = df[deposits_col] - df[withdrawals_col]
    
    return df



class DataGenerator:
    def __init__(self):
        # Transaction categories and constraints
        self.categories = {
            "Card Payment": {"min": -500, "max": -10, "frequency": (5, 10)},
            "Mortgage": {"min": -1500, "max": -3000, "frequency": 1},
            "Paycheck": {"min": 2000, "max": 4000, "frequency": (2, 4)},
            "Shopping": {"min": -200, "max": -20, "frequency": (3, 7)},
            "Streaming": {"min": -15, "max": -5, "frequency": (1, 3)},
            "Gift": {"min": -500, "max": 500, "frequency": (1, 3)},
            "Utility Bill": {"min": -200, "max": -50, "frequency": (1, 3)},
            "Commission": {"min": 500, "max": 2000, "frequency": (1, 2)},
            "Travel": {"min": -1000, "max": -200, "frequency": (0, 2)},
            "Repair": {"min": -500, "max": -50, "frequency": (0, 3)},
        }
        self.start_balance = 10000

    def generate(self):
        # Define the range of dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2) #delta = 2 years

        # Generate transactions
        data = []
        current_balance = self.start_balance

        for single_date in pd.date_range(start=start_date, end=end_date, freq="ME"):
            for category, constraints in self.categories.items():
                if category == "Mortgage":
                    # Always one mortgage payment per month
                    amount = random.uniform(constraints["min"], constraints["max"])
                    data.append(
                        {"Date": single_date, "Amount": round(amount, 2), "Description": category}
                    )
                else:
                    # Generate variable number of transactions
                    freq = random.randint(*constraints["frequency"])
                    for _ in range(freq):
                        amount = random.uniform(constraints["min"], constraints["max"])
                        # Ensure the balance doesn't drop below zero
                        if category not in ["Paycheck", "Commission"] and current_balance + amount < 0:
                            continue
                        data.append(
                            {"Date": single_date, "Amount": round(amount, 2), "Description": category}
                        )
                        current_balance += amount

        # Convert to DataFrame 
        df = pd.DataFrame(data)
        df.sort_values("Date", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Calculate running balance using cummulative sum of activity
        df["Balance"] = self.start_balance + df["Amount"].cumsum()
        return df