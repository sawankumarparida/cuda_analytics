# MUST BE AT THE ABSOLUTE TOP BEFORE ANY OTHER IMPORTS
import matplotlib
matplotlib.use('Agg') # Force Matplotlib to headless mode in WSL

import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# 1. Page Configuration
st.set_page_config(page_title="BA Automation Hub", layout="wide")
st.title("📊 Business Analyst Automation Hub")
st.markdown("A suite of automated data processing tools for cleaning, transforming, and analyzing datasets.")

# 2. Sidebar Navigation
st.sidebar.header("Select a Tool")
tool = st.sidebar.radio("Available Tools", [
    "🧹 Data Profiler & Cleaner", 
    "🔄 Format Converter (CSV ↔ Excel)", 
    "📈 Instant Pivot Table Generator"
])

# Helper function to load data safely
def load_uploaded_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        return None
        
    # FIX: Drop duplicate column names to prevent "not 1-dimensional" pivot errors
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# ==========================================
# TOOL 1: DATA PROFILER & CLEANER
# ==========================================
if tool == "🧹 Data Profiler & Cleaner":
    st.header("🧹 Data Profiler & Cleaner")
    st.markdown("Upload a messy dataset to automatically identify missing values, duplicates, and generate a cleaned file.")
    
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        df = load_uploaded_file(uploaded_file)
        
        if df is not None:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Rows", df.shape[0])
            col2.metric("Total Columns", df.shape[1])
            col3.metric("Duplicate Rows", df.duplicated().sum())
            
            st.subheader("Data Preview")
            st.dataframe(df.head())
            
            st.subheader("Missing Values Report")
            missing_data = df.isnull().sum()
            missing_data = missing_data[missing_data > 0]
            if missing_data.empty:
                st.success("No missing values found! Your dataset is clean.")
            else:
                st.warning("Found missing values in the following columns:")
                st.dataframe(missing_data.reset_index().rename(columns={'index': 'Column', 0: 'Missing Count'}))
            
            st.divider()
            st.subheader("Automated Cleaning")
            if st.button("🚀 Clean Dataset (Drop Nulls & Duplicates)"):
                clean_df = df.dropna().drop_duplicates()
                st.success(f"Cleaned! Reduced from {df.shape[0]} to {clean_df.shape[0]} rows.")
                
                # Provide download button for the cleaned data
                csv = clean_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Cleaned CSV",
                    data=csv,
                    file_name=f"cleaned_{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv"
                )

# ==========================================
# TOOL 2: FORMAT CONVERTER
# ==========================================
elif tool == "🔄 Format Converter (CSV ↔ Excel)":
    st.header("🔄 Smart Format Converter")
    st.markdown("Instantly convert massive datasets between CSV and Excel formats.")
    
    uploaded_file = st.file_uploader("Upload a file to convert", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        df = load_uploaded_file(uploaded_file)
        
        if df is not None:
            st.success(f"Successfully loaded {uploaded_file.name}")
            
            # If CSV, offer Excel download
            if uploaded_file.name.endswith('.csv'):
                st.info("File detected as CSV. Ready to convert to Excel.")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="⬇️ Download as Excel (.xlsx)",
                    data=excel_data,
                    file_name=f"{uploaded_file.name.split('.')[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            # If Excel, offer CSV download
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                st.info("File detected as Excel. Ready to convert to CSV.")
                csv_data = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="⬇️ Download as CSV",
                    data=csv_data,
                    file_name=f"{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv"
                )

# ==========================================
# TOOL 3: INSTANT PIVOT TABLE
# ==========================================
elif tool == "📈 Instant Pivot Table Generator":
    st.header("📈 Instant Pivot Table & Chart Generator")
    st.markdown("Upload raw data to dynamically group, aggregate, and visualize without writing code.")
    
    uploaded_file = st.file_uploader("Upload dataset (CSV or Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        df = load_uploaded_file(uploaded_file)
        
        if df is not None:
            col1, col2, col3 = st.columns(3)
            
            # Let user select columns for the pivot table
            index_col = col1.selectbox("Group By (Category):", options=df.columns)
            
            # Only allow numeric columns for the values
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                value_col = col2.selectbox("Value to Calculate:", options=numeric_cols)
                agg_func = col3.selectbox("Math Function:", options=["sum", "mean", "count", "max", "min"])
                
                if st.button("🚀 Generate Pivot Table"):
                    # Create the pivot table
                    pivot_df = pd.pivot_table(df, values=value_col, index=index_col, aggfunc=agg_func).reset_index()
                    pivot_df = pivot_df.sort_values(by=value_col, ascending=False)
                    
                    st.subheader("Generated Pivot Table")
                    st.dataframe(pivot_df)
                    
                    # Generate a chart
                    st.subheader("Visualization")
                    fig, ax = plt.subplots(figsize=(10, 4))
                    
                    # Plot top 10 if there are too many categories
                    plot_df = pivot_df.head(15) 
                    ax.bar(plot_df[index_col].astype(str), plot_df[value_col], color='#4C72B0')
                    plt.xticks(rotation=45, ha='right')
                    ax.set_ylabel(f"{agg_func.title()} of {value_col}")
                    ax.set_title(f"{value_col} by {index_col}")
                    
                    st.pyplot(fig)
            else:
                st.error("No numeric columns found in the dataset to aggregate!")