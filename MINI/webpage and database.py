import streamlit as st
import joblib
import pymysql
import re
from datetime import datetime
import numpy as np

# Load the trained models
xgb_model = joblib.load(
    r"C:\sd card\4-1 sem\mini project\fake job prediction\Predicting-fake-job-posts-main\Predicting-fake-job-posts-main\model\t\xgboost_model.joblib")
vectorizer = joblib.load(
    r"C:\sd card\4-1 sem\mini project\fake job prediction\Predicting-fake-job-posts-main\Predicting-fake-job-posts-main\model\t\vectorizer.pkl")

# Streamlit Web Page Title
st.title("Unmasking Employment scams")

# Define a list of fake job keywords
fake_job_keywords = [
    "work from home", "easy money", "no experience required", "part-time",
    "immediate start", "urgent hiring", "get rich quick", "high salary",
    "free training", "no interview", "apply now", "limited time offer", "fake"
]

# Initialize job_data as a dictionary
job_data = {}

# Input fields for various job details with inline descriptions
st.write("### Please fill out the details below:")

st.write("**Job Title**")
st.write("Enter the title of the job position (e.g., Software Engineer).")
job_data['title'] = st.text_input("", key="title")

st.write("**Location**")
st.write("Enter the job location (e.g., New York, Remote).")
job_data['location'] = st.text_input("", key="location")

st.write("**Salary Range**")
st.write("Enter numerical values for the salary range (e.g., 40000-60000).")
job_data['salary_range'] = st.text_input("", key="salary_range")

st.write("**Company Name**")
st.write("Provide a brief description of the company.")
job_data['company_profile'] = st.text_input("", key="company_profile")

st.write("**Job Description**")
st.write("Enter the detailed job description.")
job_data['description'] = st.text_area("", key="description")

st.write("**Requirements**")
st.write("List the skills and qualifications required for the job.")
job_data['requirements'] = st.text_area("", key="requirements")

st.write("**Telecommuting**")
st.write("Enter `1` if telecommuting is allowed, otherwise `0`.")
job_data['telecommuting'] = st.radio("", (0, 1), key="telecommuting")

st.write("**Interview Questions**")
st.write("Enter `1` if the job has pre-interview questions, otherwise `0`.")
job_data['has_questions'] = st.radio("", (0, 1), key="has_questions")

st.write("**Employment Type**")
st.write("Enter the type of employment (e.g., Full-time, Part-time).")
job_data['employment_type'] = st.text_input("", key="employment_type")

st.write("**Required Experience**")
st.write("Specify the required experience (e.g., 2-5 years).")
job_data['required_experience'] = st.text_input("", key="required_experience")

st.write("**Required Education**")
st.write("Mention the required education level (e.g., Bachelor's degree).")
job_data['required_education'] = st.text_input("", key="required_education")



# Function to check if the input contains only valid English words
def contains_only_english_words(text):
    # Skip non-string types (like integers or floats)
    if not isinstance(text, str):
        return True  # Return True for non-string types (they're not relevant for word validation)

    # Use regex to find only alphabetic words (ignores numbers and punctuation)
    words_in_text = re.findall(r'\b[a-zA-Z]+\b', text)
    for word in words_in_text:
        if not word.isalpha():  # Only allow alphabetic characters
            return False
    return True


# Function to check if the job description contains any fake job keywords
def contains_fake_keywords(text):
    text = text.lower()  # Convert text to lowercase for case-insensitive matching
    for keyword in fake_job_keywords:
        if keyword in text:  # If any keyword is found in the description, return True
            return True
    return False


# Function to preprocess text for the XGBoost model
def preprocess_text_xgb(text):
    return vectorizer.transform([text])


# Function to create a database connection
def create_connection():
    try:
        return pymysql.connect(
            host="localhost",
            user="root",  # Replace with your MySQL username
            password="",  # Replace with your MySQL password
            database="fake_job_prediction"  # Database name
        )
    except pymysql.err.OperationalError as e:
        st.error(f"Database connection failed: {e}")
        return None


# Function to create the table if it doesn’t exist
def create_table():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS job_data (
            title VARCHAR(255),
            location VARCHAR(255),
            salary_range VARCHAR(50),
            company_profile TEXT,
            description TEXT,
            requirements TEXT,
            telecommuting TINYINT,
            has_questions TINYINT,
            employment_type VARCHAR(50),
            required_experience VARCHAR(50),
            required_education VARCHAR(50),
            fraud_prediction VARCHAR(10),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()


# Call create_table() during app startup
create_table()


# Function to save data to the MySQL database
def save_to_database(data, prediction):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        sql = """
            INSERT INTO job_data (title, location, salary_range, company_profile, 
            description, requirements, telecommuting, has_questions, 
            employment_type, required_experience, required_education, fraud_prediction, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['title'], data['location'], data['salary_range'], data['company_profile'],
            data['description'], data['requirements'], data['telecommuting'],
            data['has_questions'], data['employment_type'],
            data['required_experience'], data['required_education'], prediction, datetime.now()
        )
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()


# Button for prediction
if st.button('Predict'):
    # Validate that all mandatory fields are filled and valid
    missing_or_invalid_fields = [
        key for key, value in job_data.items()
        if isinstance(value, str) and (value.strip() == "" or not contains_only_english_words(value))
        # Only check string fields for stripping
    ]
    if missing_or_invalid_fields:
        st.warning(f"Please provide valid English words for all fields: {', '.join(missing_or_invalid_fields)}")
    else:
        job_description = job_data['description']  # Get the job description from user input

        # Check if the job description contains any fake job keywords
        if contains_fake_keywords(job_description):
            prediction = "FAKE"
            st.write("Prediction: This job is **FAKE** (based on keywords)")
        else:
            # Preprocess text for XGBoost model
            xgb_input = preprocess_text_xgb(job_description)

            # Predict using XGBoost model
            xgb_prediction = xgb_model.predict(xgb_input)

            # Show the prediction results
            if xgb_prediction[0] == 1:
                prediction = "FAKE"
                st.write("Prediction: This job is **FAKE** (model)")
            else:
                prediction = "REAL"
                st.write("Prediction: This job is **REAL**")

        # Save user input and prediction to the database
        save_to_database(job_data, prediction)
        st.success("Job data saved successfully to the database!")
