"""
data_pipeline.py

Central place for loading the EduPro workbook, joining the three sheets,
and computing the KPIs listed in the project brief. Both data_analysis.py
(the offline EDA / research-paper script) and app.py (the Streamlit
dashboard) import from here so the numbers never drift between the two.
"""

import pandas as pd

DATA_PATH = "data/EduPro_Dataset.xlsx"


def load_raw(path=DATA_PATH):
    teachers = pd.read_excel(path, sheet_name="Teachers")
    courses = pd.read_excel(path, sheet_name="Courses")
    transactions = pd.read_excel(path, sheet_name="Transactions")
    return teachers, courses, transactions


def build_master_table(path=DATA_PATH):
    """
    Joins Transactions -> Courses -> Teachers into one row-per-enrollment
    table, and also returns a course-level rollup with enrollment counts.
    This is the table almost every chart/KPI in the app is built from.
    """
    teachers, courses, transactions = load_raw(path)

    enrollments = transactions.merge(courses, on="CourseID", how="left", validate="many_to_one")
    enrollments = enrollments.merge(
        teachers, on="TeacherID", how="left", validate="many_to_one", suffixes=("", "_teacher")
    )

    # sanity check: every course/teacher referenced in transactions should
    # actually exist in the master sheets
    missing_courses = enrollments["CourseName"].isna().sum()
    missing_teachers = enrollments["TeacherName"].isna().sum()
    if missing_courses or missing_teachers:
        print(
            f"Warning: {missing_courses} transactions reference an unknown course, "
            f"{missing_teachers} reference an unknown teacher."
        )

    enrollment_counts = (
        transactions.groupby("CourseID").size().rename("EnrollmentCount").reset_index()
    )

    # The Courses sheet itself has no TeacherID column -- the only place
    # course and teacher are linked is Transactions. We take the most
    # frequently associated teacher per course as "the" instructor for
    # that course (in practice a course has one instructor, so this is
    # just recovering that mapping from the enrollment log).
    course_teacher_map = (
        transactions.groupby(["CourseID", "TeacherID"]).size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .drop_duplicates("CourseID")[["CourseID", "TeacherID"]]
    )

    course_summary = courses.merge(course_teacher_map, on="CourseID", how="left")
    course_summary = course_summary.merge(enrollment_counts, on="CourseID", how="left")
    course_summary["EnrollmentCount"] = course_summary["EnrollmentCount"].fillna(0).astype(int)
    course_summary = course_summary.merge(teachers, on="TeacherID", how="left")

    return teachers, courses, transactions, enrollments, course_summary


def rating_tier(rating, low=3.5, high=4.3):
    if rating >= high:
        return "High"
    if rating >= low:
        return "Mid"
    return "Low"


def compute_kpis(teachers, courses, course_summary):
    """
    Returns the five KPIs called out in the brief as a flat dict, so both
    the CLI report and the Streamlit metric tiles can pull from one place.
    """
    avg_teacher_rating = teachers["TeacherRating"].mean()
    avg_course_rating = courses["CourseRating"].mean()

    # Rating Consistency Index: 1 - normalized std dev of a teacher's own
    # course ratings, averaged across teachers. Higher = more consistent.
    per_teacher_std = course_summary.groupby("TeacherID")["CourseRating"].std().fillna(0)
    rating_consistency_index = (1 - (per_teacher_std / 4)).clip(lower=0).mean()

    # Experience Impact Score: correlation between YearsOfExperience and
    # TeacherRating, rescaled to 0-100 for a friendlier KPI tile.
    exp_corr = teachers[["YearsOfExperience", "TeacherRating"]].corr().iloc[0, 1]
    experience_impact_score = (exp_corr + 1) / 2 * 100

    # Enrollment Influence Ratio: avg enrollments per course for
    # High-tier instructors vs Low-tier instructors.
    course_summary = course_summary.copy()
    course_summary["RatingTier"] = course_summary["TeacherRating"].apply(rating_tier)
    tier_enrollment = course_summary.groupby("RatingTier")["EnrollmentCount"].mean()
    high_avg = tier_enrollment.get("High", float("nan"))
    low_avg = tier_enrollment.get("Low", float("nan"))
    enrollment_influence_ratio = high_avg / low_avg if low_avg else float("nan")

    return {
        "Average Teacher Rating": round(avg_teacher_rating, 2),
        "Average Course Rating": round(avg_course_rating, 2),
        "Rating Consistency Index": round(rating_consistency_index, 2),
        "Experience Impact Score": round(experience_impact_score, 1),
        "Enrollment Influence Ratio": round(enrollment_influence_ratio, 2),
    }
