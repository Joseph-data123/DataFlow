import hashlib
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("DataFlow")
st.subheader("Making data analysis simple for everyone")

st.write("Welcome to DataFlow!")
st.write("Upload your dataset to begin exploring your data.")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"]
)

if uploaded_file is not None:

    file_id = hashlib.sha256(uploaded_file.getvalue()).hexdigest()

    if st.session_state.get("file_id") != file_id:
        st.session_state["file_id"] = file_id
        st.session_state["working_df"] = pd.read_csv(uploaded_file)

    df = st.session_state["working_df"]

    st.success("Dataset uploaded successfully!")

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    st.write("Number of rows:", df.shape[0])
    st.write("Number of columns:", df.shape[1])

    st.subheader("Data Quality Report")

    missing_values = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()

    st.write("Total missing values:", missing_values)
    st.write("Total duplicate rows:", duplicate_rows)

    missing_by_column = df.isnull().sum()
    missing_table = missing_by_column.reset_index()
    missing_table.columns = ["Column Name", "Missing Values"]

    st.subheader("Missing Values by Column")
    st.dataframe(missing_table, hide_index=True)

    data_types = df.dtypes.reset_index()
    data_types.columns = ["Column Name", "Data Type"]

    data_types["Data Type"] = data_types["Data Type"].astype(str)

    data_types["Data Type"] = data_types["Data Type"].replace({
        "object": "Text or Mixed Values",
        "int64": "Whole Number",
        "float64": "Decimal Number",
        "bool": "True/False",
        "datetime64[ns]": "Date and Time"
    })

    with st.expander("Understanding Your Columns"):
        st.dataframe(data_types, hide_index=True)

    st.subheader("Text Cleaning")

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns.tolist()

    if text_columns:

        selected_column = st.selectbox(
            "Choose a column to clean",
            text_columns
        )

        cleaning_option = st.selectbox(
            "Choose a cleaning operation",
            ["Title Case", "Lowercase", "Uppercase", "Remove Extra Spaces"]
        )

        original_values = df[selected_column].astype("string")

        if cleaning_option == "Title Case":
            cleaned_values = original_values.str.title()

        elif cleaning_option == "Lowercase":
            cleaned_values = original_values.str.lower()

        elif cleaning_option == "Uppercase":
            cleaned_values = original_values.str.upper()

        elif cleaning_option == "Remove Extra Spaces":
            cleaned_values = original_values.str.strip()
            cleaned_values = cleaned_values.str.replace(
                r"\s+", " ", regex=True
            )

        st.write("Preview Changes")

        preview = pd.DataFrame({
            "Before": original_values.head(),
            "After": cleaned_values.head()
        })

        st.dataframe(preview, hide_index=True)

        if st.button("Apply Changes"):
            st.session_state["working_df"][selected_column] = cleaned_values
            st.rerun()

    st.subheader("Data Visualization")

    st.write("Explore your data by creating interactive charts.")

    categorical_columns = df.select_dtypes(
        include=["object", "string", "category"]
    ).columns.tolist()

    if categorical_columns:

        chart_column = st.selectbox(
            "Choose a column to visualize",
            categorical_columns
        )

        chart_data = df[chart_column].value_counts(dropna=False).head(10).reset_index()

        chart_data.columns = ["Category", "Count"]

        fig = px.bar(
            chart_data,
            x="Category",
            y="Count",
            title=f"Top 10 Most Common Values in {chart_column}",
            text="Count"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.write(
            f"This chart shows the 10 most common values in the {chart_column} column."
        )

    else:

        st.info("No categorical columns available for visualization.")

        st.subheader("Line Chart")

    st.write("Explore how your data changes over time.")

    date_columns = [
        column for column in df.columns
        if "date" in column.lower() or "time" in column.lower()
    ]

    if date_columns:

        selected_date = st.selectbox(
            "Choose a date column",
            date_columns 
        )

        dates = pd.to_datetime(
            df[selected_date],
            errors="coerce",
            format="mixed"
        )

        chart_data = pd.DataFrame({"Date": dates}).dropna()

        if not chart_data.empty:

            chart_data["Month"] = chart_data["Date"].dt.to_period("M").dt.to_timestamp()

            monthly_data = chart_data.groupby("Month").size().reset_index(name="Count")

            fig = px.line(
                monthly_data,
                x="Month",
                y="Count",
                title=f"Monthly Trend of {selected_date}",
                markers=True
            )

            st.plotly_chart(fig, use_container_width=True)

            st.write(
                "This chart shows how the number of records changes each month."
            )

        else:

            st.warning("No valid dates were found in the selected column.")

    else:

        st.info("No date columns were detected in your dataset.")
        st.subheader("Download Your Cleaned Dataset")

    csv_data = st.session_state["working_df"].to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Cleaned CSV",
        data=csv_data,
        file_name="dataflow_cleaned.csv",
        mime="text/csv"
    )

    
    st.subheader("Duplicate Removal")

    duplicate_count = df.duplicated().sum()

    if duplicate_count > 0:

        st.warning(f"We found {duplicate_count} duplicate rows in your dataset.")

        st.write("Preview of Duplicate Records")

        duplicate_preview = df[df.duplicated(keep=False)]

        st.dataframe(duplicate_preview.head(10))

        if st.button("Remove Duplicates"):

            st.session_state["working_df"] = df.drop_duplicates().reset_index(drop=True)

            st.rerun()

    else:

        st.success("No duplicate rows found in your dataset!")
        st.subheader("Handle Missing Values")

    missing_columns = df.columns[df.isnull().any()].tolist()

    if missing_columns:

        selected_column = st.selectbox(
            "Choose a column with missing values",
            missing_columns
        )

        missing_count = df[selected_column].isnull().sum()

        st.write("Missing values in this column:", missing_count)

        if pd.api.types.is_numeric_dtype(df[selected_column]):

            if df[selected_column].notna().any():
                cleaning_options = [
                    "Remove rows with missing values",
                    "Fill with Mean",
                    "Fill with Median"
                ]
            else:
                cleaning_options = [
                    "Remove rows with missing values"
                ]

        else:

            cleaning_options = [
                "Remove rows with missing values",
                "Fill with Unknown"
            ]

        cleaning_method = st.selectbox(
            "Choose how to handle missing values",
            cleaning_options
        )

        cleaned_df = df.copy()

        if cleaning_method == "Remove rows with missing values":

            cleaned_df = df.dropna(
                subset=[selected_column]
            ).reset_index(drop=True)

            st.write(f"Rows that will be removed: {missing_count}")

            st.dataframe(
                df[df[selected_column].isnull()].head(5),
                hide_index=True
            )

        else:

            if cleaning_method == "Fill with Mean":
                fill_value = df[selected_column].mean()

            elif cleaning_method == "Fill with Median":
                fill_value = df[selected_column].median()

            else:
                fill_value = "Unknown"

            cleaned_df[selected_column] = df[selected_column].fillna(
                fill_value
            )

            affected_rows = df[df[selected_column].isnull()].head(5)

            preview = pd.DataFrame({
                "Before": affected_rows[selected_column],
                "After": cleaned_df.loc[
                    affected_rows.index, selected_column
                ]
            })

            st.write("Preview Changes")
            st.dataframe(preview, hide_index=True)

        if st.button("Apply Missing Value Fix"):

            st.session_state["working_df"] = cleaned_df

            st.rerun()

    else:

        st.success("No missing values found in your dataset!")
