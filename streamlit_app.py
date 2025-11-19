import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Tutor Matcher", page_icon="📚", layout="wide")

def format_subject(subject):
    """Format subject - extract course code if present, otherwise keep as is"""
    subject = subject.strip()
    course_code_match = re.match(r'^([A-Za-z]{4})[-\s]?(\d{4})', subject)
    
    if course_code_match:
        letters = course_code_match.group(1).upper()
        numbers = course_code_match.group(2)
        return f"{letters}{numbers}"
    else:
        return subject

def process_files(staff_file, appointments_file):
    # Read the tutor availability Excel file
    tutor_df = pd.read_excel(staff_file, header=1)
    
    # Filter for tutors only
    tutor_mask = tutor_df['Position'].astype(str).str.contains('Content Tutor|Tutor', case=False, na=False, regex=True)
    tutors_df = tutor_df[tutor_mask]
    
    # Build a dictionary of course codes to tutors
    course_to_tutors = {}
    for idx, row in tutors_df.iterrows():
        tutor_name = row['Name'] if 'Name' in tutor_df.columns else row.iloc[0]
        
        # Skip if tutor name is not a string or is a number
        if pd.isna(tutor_name) or isinstance(tutor_name, (int, float)):
            continue
        
        tutor_name = str(tutor_name)
        subjects = row['Content Tutor Subject'] if 'Content Tutor Subject' in tutor_df.columns else ''
        
        if pd.notna(subjects):
            subject_list = re.split('[,;:/]', str(subjects))
            for subject in subject_list:
                if subject.strip():
                    formatted_subject = format_subject(subject)
                    if formatted_subject not in course_to_tutors:
                        course_to_tutors[formatted_subject] = []
                    course_to_tutors[formatted_subject].append(tutor_name)
    
    # Read the appointments Excel file
    appointment_df = pd.read_excel(appointments_file)
    
    # Filter for tutoring appointments only
    tutoring_mask = appointment_df['Requested Service'].astype(str).str.contains('tutoring appointment', case=False, na=False)
    tutoring_df = appointment_df[tutoring_mask]
    
    # Group by student name and collect all their courses
    student_courses = {}
    for idx, row in tutoring_df.iterrows():
        student_name = str(row.iloc[0])  # First column is student name
        
        # Try to find the course column
        course = None
        if 'Requested Course Number' in appointment_df.columns:
            course = row['Requested Course Number']
        elif 'Requested Course' in appointment_df.columns:
            course = row['Requested Course']
        else:
            # Try to find any column with 'course' in the name
            course_cols = [col for col in appointment_df.columns if 'course' in col.lower()]
            if course_cols:
                course = row[course_cols[0]]
        
        if student_name not in student_courses:
            student_courses[student_name] = []
        
        if pd.notna(course):
            course_formatted = str(course).replace('-', '').upper()
            student_courses[student_name].append(course_formatted)
    
    return student_courses, course_to_tutors

# Streamlit UI
st.title("📚 Tutor Matching System")
st.markdown("Upload your Excel files to match students with available tutors.")

# Create two columns for file uploaders
col1, col2 = st.columns(2)

with col1:
    st.subheader("Staff Availability File")
    staff_file = st.file_uploader("Upload Staff Excel File", type=['xlsx', 'xls'], key="staff")

with col2:
    st.subheader("Appointments File")
    appointments_file = st.file_uploader("Upload Appointments Excel File", type=['xlsx', 'xls'], key="appointments")

# Process button
if staff_file and appointments_file:
    if st.button("🔍 Match Tutors to Students", type="primary"):
        with st.spinner("Processing files..."):
            try:
                student_courses, course_to_tutors = process_files(staff_file, appointments_file)
                
                st.success("✅ Matching completed successfully!")
                
                # Display results
                st.markdown("---")
                st.header("Tutoring Appointment Requests")
                
                for student_name, courses in student_courses.items():
                    with st.expander(f"📘 {student_name}", expanded=True):
                        if courses:
                            for course in courses:
                                # Find available tutors for this course
                                available_tutors = course_to_tutors.get(course, [])
                                
                                if available_tutors:
                                    tutors_list = ", ".join(available_tutors)
                                    st.markdown(f"**{course}:** {tutors_list}")
                                else:
                                    st.markdown(f"**{course}:** ⚠️ No tutors available")
                        else:
                            st.warning("No course specified")
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.exception(e)
else:
    st.info("👆 Please upload both Excel files to begin matching.")

# Footer
st.markdown("---")
st.caption("Tutor Matching System | Upload your files to get started")
