import hashlib
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="DataFlow | Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.title("DataFlow")
    st.caption("Your data analysis workspace")
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload your CSV",
        type=["csv"]
    )

    if uploaded_file is not None:
        section = st.radio(
            "Navigate",
            ["Overview", "Data Quality", "Cleaning", "Visualization", "Download"],
            key="navigation"
        )
    else:
        section = "Overview"
        st.info("Upload a CSV to begin.")

    st.divider()
    st.caption("Review • Clean • Visualize")

if uploaded_file is None:
    st.title("Welcome to DataFlow")
    st.caption("Making data analysis simple for everyone")
    st.subheader("Turn your data into clear insights")
    st.write(
        "Upload a CSV using the sidebar, then review its quality, "
        "clean your records, and explore interactive charts."
    )

    preview_column, cleaning_column, chart_column = st.columns(3)

    with preview_column:
        with st.container(border=True):
            st.subheader("Review")
            st.write("See your dataset and check missing values and duplicates.")

    with cleaning_column:
        with st.container(border=True):
            st.subheader("Clean")
            st.write("Standardize text, remove duplicates, and handle missing values.")

    with chart_column:
        with st.container(border=True):
            st.subheader("Explore")
            st.write("Create bar and line charts, then download your cleaned CSV.")

else:
    file_id = hashlib.sha256(uploaded_file.getvalue()).hexdigest()

    if st.session_state.get("file_id") != file_id:
        loaded_df = pd.read_csv(uploaded_file)
        st.session_state["file_id"] = file_id
        st.session_state["working_df"] = loaded_df

    df = st.session_state["working_df"]
    missing_values = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()

    descriptions = {
        "Overview": "Your dataset at a glance.",
        "Data Quality": "Understand missing values, duplicates, and column types.",
        "Cleaning": "Preview and apply changes to your working dataset.",
        "Visualization": "Explore categories and trends over time.",
        "Download": "Export your current working dataset."
    }

    st.title(section)
    st.caption(f"Dataset: {uploaded_file.name}")
    st.write(descriptions[section])
    st.divider()

    if section == "Overview":
        row_card, column_card, missing_card, duplicate_card = st.columns(4)

        with row_card:
            with st.container(border=True):
                st.metric("Rows", f"{df.shape[0]:,}")

        with column_card:
            with st.container(border=True):
                st.metric("Columns", f"{df.shape[1]:,}")

        with missing_card:
            with st.container(border=True):
                st.metric("Missing Values", f"{missing_values:,}")

        with duplicate_card:
            with st.container(border=True):
                st.metric("Duplicate Rows", f"{duplicate_rows:,}")

        st.subheader("Dataset Preview")
        st.dataframe(df.head(), use_container_width=True)
        st.info("Choose a section in the sidebar to continue.")

    elif section == "Data Quality":
        missing_card, duplicate_card = st.columns(2)

        with missing_card:
            with st.container(border=True):
                st.metric("Missing Values", f"{missing_values:,}")

        with duplicate_card:
            with st.container(border=True):
                st.metric("Duplicate Rows", f"{duplicate_rows:,}")

        missing_table = df.isnull().sum().reset_index()
        missing_table.columns = ["Column Name", "Missing Values"]

        st.subheader("Missing Values by Column")
        st.dataframe(
            missing_table,
            hide_index=True,
            use_container_width=True
        )

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
            st.dataframe(
                data_types,
                hide_index=True,
                use_container_width=True
            )

    elif section == "Cleaning":
        st.subheader("Text Cleaning")

        text_columns = df.select_dtypes(
            include=["object", "string"]
        ).columns.tolist()

        if text_columns:
            selected_column = st.selectbox(
                "Choose a column to clean",
                text_columns,
                key="text_column"
            )

            cleaning_option = st.selectbox(
                "Choose a cleaning operation",
                ["Title Case", "Lowercase", "Uppercase", "Remove Extra Spaces"],
                key="text_operation"
            )

            original_values = df[selected_column].astype("string")

            if cleaning_option == "Title Case":
                cleaned_values = original_values.str.title()
            elif cleaning_option == "Lowercase":
                cleaned_values = original_values.str.lower()
            elif cleaning_option == "Uppercase":
                cleaned_values = original_values.str.upper()
            else:
                cleaned_values = original_values.str.strip()
                cleaned_values = cleaned_values.str.replace(
                    r"\s+", " ", regex=True
                )

            preview = pd.DataFrame({
                "Before": original_values.head(),
                "After": cleaned_values.head()
            })

            st.write("Preview Changes")
            st.dataframe(
                preview,
                hide_index=True,
                use_container_width=True
            )

            if st.button("Apply Changes", key="apply_text"):
                st.session_state["working_df"][selected_column] = cleaned_values
                st.rerun()
        else:
            st.info("No text columns available for cleaning.")

        st.divider()
        st.subheader("Duplicate Removal")

        if duplicate_rows > 0:
            st.warning(
                f"We found {duplicate_rows:,} duplicate rows in your dataset."
            )
            st.write("Preview of Duplicate Records")

            duplicate_preview = df[df.duplicated(keep=False)]
            st.dataframe(
                duplicate_preview.head(10),
                use_container_width=True
            )

            if st.button("Remove Duplicates", key="remove_duplicates"):
                st.session_state["working_df"] = (
                    df.drop_duplicates().reset_index(drop=True)
                )
                st.rerun()
        else:
            st.success("No duplicate rows found in your dataset!")

        st.divider()
        st.subheader("Handle Missing Values")

        missing_columns = df.columns[df.isnull().any()].tolist()

        if missing_columns:
            selected_column = st.selectbox(
                "Choose a column with missing values",
                missing_columns,
                key="missing_column"
            )

            missing_count = df[selected_column].isnull().sum()
            st.write("Missing values in this column:", int(missing_count))

            if pd.api.types.is_numeric_dtype(df[selected_column]):
                cleaning_options = ["Remove rows with missing values"]

                if df[selected_column].notna().any():
                    cleaning_options += ["Fill with Mean", "Fill with Median"]
            else:
                cleaning_options = [
                    "Remove rows with missing values",
                    "Fill with Unknown"
                ]

            cleaning_method = st.selectbox(
                "Choose how to handle missing values",
                cleaning_options,
                key="missing_method"
            )

            cleaned_df = df.copy()

            if cleaning_method == "Remove rows with missing values":
                cleaned_df = df.dropna(
                    subset=[selected_column]
                ).reset_index(drop=True)

                st.write(f"Rows that will be removed: {missing_count:,}")
                st.dataframe(
                    df[df[selected_column].isnull()].head(5),
                    hide_index=True,
                    use_container_width=True
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
                st.dataframe(
                    preview,
                    hide_index=True,
                    use_container_width=True
                )

            if st.button("Apply Missing Value Fix", key="apply_missing"):
                st.session_state["working_df"] = cleaned_df
                st.rerun()
        else:
            st.success("No missing values found in your dataset!")

    elif section == "Visualization":
        st.subheader("Bar Chart")

        categorical_columns = df.select_dtypes(
            include=["object", "string", "category"]
        ).columns.tolist()

        if categorical_columns:
            chart_column = st.selectbox(
                "Choose a column to visualize",
                categorical_columns,
                key="bar_column"
            )

            chart_data = (
                df[chart_column]
                .value_counts(dropna=False)
                .head(10)
                .reset_index()
            )
            chart_data.columns = ["Category", "Count"]

            fig = px.bar(
                chart_data,
                x="Category",
                y="Count",
                title=f"Top 10 Most Common Values in {chart_column}",
                text="Count",
                color_discrete_sequence=["#0F766E"]
            )

            st.plotly_chart(fig, use_container_width=True)
            st.write(
                f"This chart shows the 10 most common values "
                f"in the {chart_column} column."
            )
        else:
            st.info("No categorical columns available for visualization.")

        st.divider()
        st.subheader("Line Chart")
        st.write("Explore how the number of records changes over time.")

        date_columns = [
            column for column in df.columns
            if "date" in column.lower()
            or "time" in column.lower()
            or column.strip().lower() == "year"
        ]

        if date_columns:
            selected_date = st.selectbox(
                "Choose a date or year column",
                date_columns,
                key="date_column"
            )

            is_year_column = selected_date.strip().lower() == "year"

            if is_year_column:
                year_values = (
                    df[selected_date]
                    .astype("string")
                    .str.strip()
                    .str.replace(r"\.0$", "", regex=True)
                )

                dates = pd.to_datetime(
                    year_values,
                    format="%Y",
                    errors="coerce"
                )
            else:
                dates = pd.to_datetime(
                    df[selected_date],
                    errors="coerce",
                    format="mixed"
                )

            chart_data = pd.DataFrame({"Date": dates}).dropna()

            if not chart_data.empty:
                if is_year_column:
                    chart_data["Year"] = chart_data["Date"].dt.year
                    trend_data = (
                        chart_data.groupby("Year")
                        .size()
                        .reset_index(name="Count")
                    )
                    time_axis = "Year"
                    chart_title = f"Yearly Record Count by {selected_date}"
                else:
                    chart_data["Month"] = (
                        chart_data["Date"].dt.to_period("M").dt.to_timestamp()
                    )
                    trend_data = (
                        chart_data.groupby("Month")
                        .size()
                        .reset_index(name="Count")
                    )
                    time_axis = "Month"
                    chart_title = f"Monthly Trend of {selected_date}"

                fig = px.line(
                    trend_data,
                    x=time_axis,
                    y="Count",
                    title=chart_title,
                    markers=True,
                    color_discrete_sequence=["#0F766E"]
                )

                if is_year_column:
                    fig.update_xaxes(tickformat="d")

                st.plotly_chart(fig, use_container_width=True)
                st.write(
                    "This chart counts records in each "
                    + ("year." if is_year_column else "month.")
                )
            else:
                st.warning(
                    "No valid dates or years were found in the selected column."
                )
        else:
            st.info("No date or year columns were detected in your dataset.")

    elif section == "Download":
        st.subheader("Your Cleaned Dataset")
        st.write(
            "This download includes all cleaning changes "
            "you have applied during this session."
        )

        st.dataframe(
            df.head(),
            use_container_width=True
        )

        csv_data = (
            st.session_state["working_df"]
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            label="Download Cleaned CSV",
            data=csv_data,
            file_name="dataflow_cleaned.csv",
            mime="text/csv",
            type="primary"
        )