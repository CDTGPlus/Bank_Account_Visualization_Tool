import streamlit as st
from data_manager import DataManager
from ui_manager import UIManager

st.set_page_config(page_title="Visual Manager", page_icon=":money_with_wings:")

st.title("Personal Finance Manager")
st.write("Generate visual summary of account activity")

# Initialize managers
data_manager = DataManager()
ui_manager = UIManager(data_manager)

# Data Source Selection
data_source = st.sidebar.radio("Choose a data source:", ("Upload File", "Generate Random Data"))

if data_source == "Upload File":
    adv = st.checkbox("Advanced")
    ui_manager.show_advanced_description(adv)
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"], key="uploaded_file")
    if uploaded_file:
        with st.spinner("Loading uploaded file..."):
            data_manager.load_uploaded_file(uploaded_file, advanced=adv)
else:
    with st.spinner("Generating synthetic data..."):
        data_manager.load_synthetic_data()

# Display and process data
if data_manager.original_data is not None:
    with st.expander("Original Data Preview", expanded=False):
        ui_manager.display_original_data()
    if ui_manager.assign_columns_and_range():
        with st.spinner("Processing derived data..."):
            data_manager.generate_derived_data()

# Display derived data and analytics
if (
    "derived_data" in st.session_state
    and st.session_state["derived_data"] is not None
    and not st.session_state["derived_data"].empty
):
    ui_manager.display_date_range_selector()
    with st.expander("View Transformed Data", expanded=False):
        ui_manager.display_derived_data()
    with st.spinner("Rendering account activity chart..."):
        ui_manager.display_account_activity_graph()
    with st.spinner("Rendering income and expense summaries..."):
        ui_manager.display_income_expense_summary()
    with st.spinner("Rendering balance trend graph..."):
        ui_manager.display_balance_graph()
else:
    st.info("No derived data available. Please upload a file and generate derived data.")


