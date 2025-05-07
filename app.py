import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load your data
@st.cache_data
def load_data():
    """Loads the data from the CSV file."""
    try:
        df = pd.read_csv('diabetes_dataset.csv')
    except FileNotFoundError:
        st.error("Error: File not found. Please make sure 'your_data.csv' is in the same directory or provide the correct path.")
        return None
    # Basic data cleaning (handle errors gracefully)
    for col in ['year', 'age']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    for col in ['hypertension', 'heart_disease', 'smoking', 'obesity', 'high_cholesterol', 'high_blood_glucose', 'diabetes']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()
            df[col] = df[col].map({'yes': 1, 'no': 0, '1': 1, '0': 0}) #handle 1/0
    return df

df = load_data()

if df is None:
    st.stop()  # Stop if the data didn't load

# --- Helper Functions ---
def create_demographic_plots(filtered_df, race_options):
    """Creates demographic distribution plots (Gender, Age, Race)."""
    # --- Gender Distribution ---
    if 'gender' in filtered_df.columns:
        gender_counts = filtered_df['gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        fig_gender = px.bar(gender_counts, x='Gender', y='Count', title='Gender Distribution')
        st.plotly_chart(fig_gender)
    else:
        st.write("Gender data is not available.")

    # --- Age Distribution ---
    if 'age' in filtered_df.columns:
        fig_age = px.histogram(filtered_df, x='age', nbins=20, title='Age Distribution')
        st.plotly_chart(fig_age)
    else:
        st.write("Age data is not available.")

    # --- Race Distribution ---
    if any(race_col in filtered_df.columns for race_col in race_options):
        race_data = {}
        for race_col in race_options:
            if race_col in filtered_df.columns:
                race_data[race_col] = filtered_df[race_col].sum()
        race_df = pd.DataFrame(list(race_data.items()), columns=['Race', 'Count'])
        if not race_df.empty:
            fig_race = px.bar(race_df, x='Race', y='Count', title='Race Distribution')
            st.plotly_chart(fig_race)
        else:
            st.write("No race data available for selected filters.")
    else:
        st.write("Race/Ethnicity data is not available.")



def create_condition_prevalence_plots(filtered_df, condition_cols):
    """Creates plots showing the prevalence of health conditions."""
    for condition in condition_cols:
        if condition in filtered_df.columns:
            condition_counts = filtered_df[condition].value_counts().reset_index()
            condition_counts.columns = ['Condition_Status', 'Count']
            condition_counts['Condition_Status'] = condition_counts['Condition_Status'].map({1: 'Yes', 0: 'No'})
            fig = px.bar(condition_counts, x='Condition_Status', y='Count',
                           title=f'Prevalence of {condition.title()}')
            st.plotly_chart(fig)
        else:
            st.write(f"{condition.title()} data is not available.")



def create_condition_relationship_plots(filtered_df, condition_cols):
    """Creates plots showing relationships between conditions and demographics."""

    for condition in condition_cols:
        if condition in filtered_df.columns and 'age' in filtered_df.columns:
            fig_age_condition = px.box(filtered_df, x=condition, y='age',
                                         title=f'Age vs. {condition.title()}')
            st.plotly_chart(fig_age_condition)

    if 'gender' in filtered_df.columns:
        gender_condition_data = {}
        for condition in condition_cols:
            if condition in filtered_df.columns:
                gender_condition_data[condition] = filtered_df.groupby('gender')[condition].mean().reset_index()
        if gender_condition_data: #check if not empty
            fig = make_subplots(rows=len(gender_condition_data), cols=1,
                                subplot_titles=[f"Gender vs. {condition.title()}" for condition in gender_condition_data])
            for i, condition in enumerate(gender_condition_data):
                fig.add_trace(go.Bar(x=gender_condition_data[condition]['gender'], y=gender_condition_data[condition][condition], name=condition), row=i+1, col=1)
            fig.update_layout(height=200 * len(gender_condition_data), showlegend=False)
            st.plotly_chart(fig)
        else:
            st.write("No conditions available to plot vs gender")
    else:
        st.write("Gender data not available")

def create_location_plots(filtered_df):
    """Creates plots related to location data."""
    if 'location' in filtered_df.columns:
        location_counts = filtered_df['location'].value_counts().reset_index()
        location_counts.columns = ['Location', 'Count']
        fig_location = px.bar(location_counts, x='Location', y='Count', title='Distribution of Records by Location')
        st.plotly_chart(fig_location)
    else:
        st.write("Location data is not available.")



# --- Main App ---
def main():
    """Main function to run the Streamlit app."""
    st.title('Health Data Visualization Dashboard')

    # --- Sidebar Filters ---
    st.sidebar.header('Filters')

    # --- Unique Options (handle missing columns gracefully) ---
    gender_options = ['All'] + (list(df['gender'].dropna().unique()) if 'gender' in df.columns else [])
    location_options = ['All'] + (list(df['location'].dropna().unique()) if 'location' in df.columns else [])
    race_options = ['race', 'race_ethic', 'race_asian', 'race_caucasian', 'race_hispanic', 'race_other']
    available_race_options = [col for col in race_options if col in df.columns] #list of available race cols
    # --- Select Filters ---
    selected_gender = st.sidebar.selectbox('Select Gender', gender_options)
    selected_location = st.sidebar.selectbox('Select Location', location_options)
    selected_race = st.sidebar.selectbox('Select Race/Ethnicity', ['All', *available_race_options])

    # --- Filter Data ---
    filtered_df = df.copy()  # Start with a copy to avoid modifying the original
    if selected_gender != 'All' and 'gender' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['gender'] == selected_gender]
    if selected_location != 'All' and 'location' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    if selected_race != 'All' and selected_race in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[selected_race] == 1] # Assuming 1 represents 'yes'


    # --- Visualization Sections ---
    st.header('Demographic Analysis')
    create_demographic_plots(filtered_df, available_race_options)

    st.header('Prevalence of Health Conditions')
    condition_cols = ['hypertension', 'heart_disease', 'smoking', 'obesity', 'high_cholesterol', 'high_blood_glucose', 'diabetes']
    create_condition_prevalence_plots(filtered_df, condition_cols)

    st.header('Relationships Between Conditions and Demographics')
    create_condition_relationship_plots(filtered_df, condition_cols)

    st.header('Location Analysis')
    create_location_plots(filtered_df)



if __name__ == '__main__':
    main()
