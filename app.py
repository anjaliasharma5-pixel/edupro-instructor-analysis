"""
app.py

Streamlit dashboard for the "Instructor Performance and Course Quality
Evaluation on EduPro" project.

Run with:
    streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from data_pipeline import build_master_table, compute_kpis, rating_tier

st.set_page_config(
    page_title="EduPro | Instructor & Course Quality",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    teachers, courses, transactions, enrollments, course_summary = build_master_table()
    course_summary["RatingTier"] = course_summary["TeacherRating"].apply(rating_tier)
    return teachers, courses, transactions, enrollments, course_summary


teachers, courses, transactions, enrollments, course_summary = load_data()

# ---------------------------------------------------------------- sidebar --
st.sidebar.header("Filters")

expertise_options = sorted(teachers["Expertise"].dropna().unique())
selected_expertise = st.sidebar.multiselect(
    "Instructor expertise", expertise_options, default=expertise_options
)

category_options = sorted(courses["CourseCategory"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Course category", category_options, default=category_options
)

level_options = sorted(courses["CourseLevel"].dropna().unique())
selected_levels = st.sidebar.multiselect(
    "Course level", level_options, default=level_options
)

rating_range = st.sidebar.slider(
    "Course rating range", min_value=1.0, max_value=5.0, value=(1.0, 5.0), step=0.1
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"{len(teachers)} instructors · {len(courses)} courses · "
    f"{len(transactions)} enrollments loaded"
)

filtered = course_summary[
    course_summary["Expertise"].isin(selected_expertise)
    & course_summary["CourseCategory"].isin(selected_categories)
    & course_summary["CourseLevel"].isin(selected_levels)
    & course_summary["CourseRating"].between(*rating_range)
]

filtered_teachers = teachers[teachers["Expertise"].isin(selected_expertise)]

# ------------------------------------------------------------------ title --
st.title("📊 Instructor Performance & Course Quality — EduPro")
st.caption(
    "Data-driven evaluation of instructor effectiveness and course quality "
    "consistency across the EduPro platform."
)

# --------------------------------------------------------------- KPI row --
kpis = compute_kpis(filtered_teachers, filtered, filtered)
kpi_cols = st.columns(5)
kpi_labels = [
    ("Average Teacher Rating", "⭐"),
    ("Average Course Rating", "📘"),
    ("Rating Consistency Index", "🎯"),
    ("Experience Impact Score", "📈"),
    ("Enrollment Influence Ratio", "👥"),
]
for col, (label, icon) in zip(kpi_cols, kpi_labels):
    col.metric(f"{icon} {label}", kpis.get(label, "—"))

st.markdown("---")

tab_leaderboard, tab_experience, tab_quality, tab_expertise = st.tabs(
    ["🏆 Instructor Leaderboard", "📈 Experience vs Rating",
     "🔥 Course Quality Heatmap", "🧭 Expertise Comparison"]
)

# ---------------------------------------------------------- leaderboard --
with tab_leaderboard:
    st.subheader("Instructor performance leaderboard")

    leaderboard = (
        filtered.groupby(["TeacherID", "TeacherName", "Expertise"])
        .agg(
            AvgCourseRating=("CourseRating", "mean"),
            TeacherRating=("TeacherRating", "first"),
            CoursesTaught=("CourseID", "nunique"),
            TotalEnrollments=("EnrollmentCount", "sum"),
        )
        .reset_index()
        .sort_values("AvgCourseRating", ascending=False)
    )
    leaderboard["AvgCourseRating"] = leaderboard["AvgCourseRating"].round(2)

    top_n = st.slider("Show top N instructors", 5, min(50, len(leaderboard)) or 5, 15)

    st.dataframe(
        leaderboard.head(top_n).rename(columns={
            "TeacherName": "Instructor",
            "Expertise": "Expertise",
            "AvgCourseRating": "Avg Course Rating",
            "TeacherRating": "Teacher Rating",
            "CoursesTaught": "Courses Taught",
            "TotalEnrollments": "Total Enrollments",
        }),
        use_container_width=True,
        hide_index=True,
    )

    fig = px.bar(
        leaderboard.head(top_n),
        x="AvgCourseRating", y="TeacherName", color="Expertise",
        orientation="h", title="Top instructors by average course rating",
        labels={"AvgCourseRating": "Avg Course Rating", "TeacherName": "Instructor"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------ experience --
with tab_experience:
    st.subheader("Does experience translate into better ratings?")

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.scatter(
            filtered_teachers, x="YearsOfExperience", y="TeacherRating",
            trendline="ols", color="Expertise",
            title="Years of Experience vs Teacher Rating",
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.scatter(
            filtered, x="YearsOfExperience", y="CourseRating",
            trendline="ols", color="CourseCategory",
            title="Years of Experience vs Course Rating",
        )
        st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.scatter(
        filtered, x="TeacherRating", y="CourseRating",
        trendline="ols", color="RatingTier",
        title="Teacher Rating vs Course Rating",
        color_discrete_map={"High": "#2ca02c", "Mid": "#ff7f0e", "Low": "#d62728"},
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Enrollment volume by instructor rating tier")
    fig4 = px.box(
        filtered, x="RatingTier", y="EnrollmentCount", color="RatingTier",
        category_orders={"RatingTier": ["Low", "Mid", "High"]},
        color_discrete_map={"High": "#2ca02c", "Mid": "#ff7f0e", "Low": "#d62728"},
    )
    st.plotly_chart(fig4, use_container_width=True)

# ----------------------------------------------------------------- quality --
with tab_quality:
    st.subheader("Course rating: category vs level")

    pivot = filtered.pivot_table(
        index="CourseCategory", columns="CourseLevel", values="CourseRating", aggfunc="mean"
    ).round(2)

    fig5 = px.imshow(
        pivot, text_auto=True, color_continuous_scale="YlGnBu",
        aspect="auto", labels=dict(color="Avg Rating"),
        title="Average course rating by category and level",
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("Rating spread by category")
    fig6 = px.violin(
        filtered, x="CourseCategory", y="CourseRating", box=True, points=False,
    )
    fig6.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig6, use_container_width=True)

    st.subheader("Gender vs course level")
    gender_level = (
        filtered.groupby(["Gender", "CourseLevel"])["CourseRating"]
        .mean().reset_index().round(2)
    )
    fig7 = px.bar(
        gender_level, x="CourseLevel", y="CourseRating", color="Gender",
        barmode="group", title="Average course rating by gender and level",
    )
    st.plotly_chart(fig7, use_container_width=True)

# -------------------------------------------------------------- expertise --
with tab_expertise:
    st.subheader("Expertise-wise performance comparison")

    expertise_summary = (
        filtered.groupby("Expertise")
        .agg(
            AvgCourseRating=("CourseRating", "mean"),
            RatingStd=("CourseRating", "std"),
            CourseCount=("CourseID", "nunique"),
            TotalEnrollments=("EnrollmentCount", "sum"),
        )
        .round(2)
        .sort_values("AvgCourseRating", ascending=False)
        .reset_index()
    )

    fig8 = px.bar(
        expertise_summary, x="AvgCourseRating", y="Expertise", orientation="h",
        error_x="RatingStd", title="Average course rating by expertise (± std dev)",
    )
    fig8.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig8, use_container_width=True)

    st.dataframe(
        expertise_summary.rename(columns={
            "AvgCourseRating": "Avg Course Rating",
            "RatingStd": "Rating Std Dev",
            "CourseCount": "Courses",
            "TotalEnrollments": "Total Enrollments",
        }),
        use_container_width=True,
        hide_index=True,
    )

    fig9 = px.scatter(
        expertise_summary, x="CourseCount", y="AvgCourseRating", size="TotalEnrollments",
        color="Expertise", title="Course volume vs quality by expertise",
        labels={"CourseCount": "Number of Courses", "AvgCourseRating": "Avg Course Rating"},
    )
    st.plotly_chart(fig9, use_container_width=True)

st.markdown("---")
st.caption(
    "EduPro Instructor & Course Quality Evaluation · Unified Mentor Pvt. Ltd. project"
)
