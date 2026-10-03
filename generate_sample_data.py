"""
generate_sample_data.py

Creates a synthetic EduPro_Dataset.xlsx with three sheets: Teachers, Courses,
Transactions -- matching the schema used in the project brief.

Only needed for local testing / demo. Once the real EduPro export is
available, drop it into data/EduPro_Dataset.xlsx with the same sheet names
and column headers and everything downstream (data_analysis.py, app.py)
keeps working without changes.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

EXPERTISE_AREAS = [
    "Data Science", "Web Development", "Digital Marketing", "Finance",
    "Graphic Design", "Business Analytics", "Cloud Computing", "Cybersecurity",
]

CATEGORIES = [
    "Data Science", "Web Development", "Marketing", "Finance",
    "Design", "Business", "Cloud & DevOps", "Security",
]

LEVELS = ["Beginner", "Intermediate", "Advanced"]

N_TEACHERS = 120
N_COURSES = 300
N_TRANSACTIONS = 8000


def build_teachers():
    teacher_ids = [f"T{str(i).zfill(4)}" for i in range(1, N_TEACHERS + 1)]
    experience = np.random.randint(1, 21, N_TEACHERS)

    # bake in a soft experience -> rating relationship with diminishing
    # returns and noise, so the "does experience help" question has a
    # real answer to find instead of pure noise
    base_rating = 3.0 + 1.6 * (1 - np.exp(-experience / 8)) + np.random.normal(0, 0.35, N_TEACHERS)
    rating = np.clip(base_rating, 1.0, 5.0).round(2)

    df = pd.DataFrame({
        "TeacherID": teacher_ids,
        "TeacherName": [f"Instructor {i}" for i in range(1, N_TEACHERS + 1)],
        "Age": np.random.randint(24, 62, N_TEACHERS),
        "Gender": np.random.choice(["Male", "Female"], N_TEACHERS, p=[0.58, 0.42]),
        "Expertise": np.random.choice(EXPERTISE_AREAS, N_TEACHERS),
        "YearsOfExperience": experience,
        "TeacherRating": rating,
    })
    return df


def build_courses(teachers_df):
    course_ids = [f"C{str(i).zfill(4)}" for i in range(1, N_COURSES + 1)]
    assigned_teachers = np.random.choice(teachers_df["TeacherID"], N_COURSES)

    teacher_rating_lookup = teachers_df.set_index("TeacherID")["TeacherRating"]
    linked_teacher_rating = assigned_teachers
    linked_teacher_rating = np.array([teacher_rating_lookup[t] for t in assigned_teachers])

    # course rating correlates with the assigned instructor's rating,
    # plus category/level noise -- mirrors a real "instructor drives
    # course quality" pattern without being a perfect 1:1 copy
    course_rating = np.clip(
        0.55 * linked_teacher_rating + 0.45 * np.random.normal(3.6, 0.6, N_COURSES),
        1.0, 5.0
    ).round(2)

    df = pd.DataFrame({
        "CourseID": course_ids,
        "CourseName": [f"Course {i}" for i in range(1, N_COURSES + 1)],
        "CourseCategory": np.random.choice(CATEGORIES, N_COURSES),
        "CourseLevel": np.random.choice(LEVELS, N_COURSES, p=[0.4, 0.4, 0.2]),
        "CourseRating": course_rating,
        "_TeacherID": assigned_teachers,  # internal helper, dropped before saving
    })
    return df


def build_transactions(courses_df):
    course_to_teacher = courses_df.set_index("CourseID")["_TeacherID"]
    course_ids = courses_df["CourseID"].values

    # popular / higher rated courses get sampled more often to create a
    # believable enrollment-skew instead of uniform random noise
    weights = courses_df["CourseRating"].values ** 3
    weights = weights / weights.sum()

    sampled_courses = np.random.choice(course_ids, N_TRANSACTIONS, p=weights)
    sampled_teachers = [course_to_teacher[c] for c in sampled_courses]

    df = pd.DataFrame({
        "TransactionID": [f"TXN{str(i).zfill(6)}" for i in range(1, N_TRANSACTIONS + 1)],
        "CourseID": sampled_courses,
        "TeacherID": sampled_teachers,
    })
    return df


def main():
    teachers_df = build_teachers()
    courses_df = build_courses(teachers_df)
    transactions_df = build_transactions(courses_df)

    courses_export = courses_df.drop(columns=["_TeacherID"])

    out_path = "data/EduPro_Dataset.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        teachers_df.to_excel(writer, sheet_name="Teachers", index=False)
        courses_export.to_excel(writer, sheet_name="Courses", index=False)
        transactions_df.to_excel(writer, sheet_name="Transactions", index=False)

    print(f"Sample dataset written to {out_path}")
    print(f"  Teachers:     {len(teachers_df)} rows")
    print(f"  Courses:      {len(courses_export)} rows")
    print(f"  Transactions: {len(transactions_df)} rows")


if __name__ == "__main__":
    main()
