"""
data_analysis.py

Offline exploratory analysis for the "Instructor Performance and Course
Quality Evaluation" project. Run this once to:
  - answer each key analytical question from the brief
  - save the supporting charts to outputs/
  - print a KPI summary you can paste straight into the research paper /
    executive summary

Usage:
    python data_analysis.py
"""

import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from data_pipeline import build_master_table, compute_kpis, rating_tier

sns.set_theme(style="whitegrid")
OUT_DIR = "outputs"


def q1_instructor_rating_distribution(teachers):
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(teachers["TeacherRating"], bins=20, kde=True, ax=ax, color="#4C72B0")
    ax.set_title("Distribution of Instructor Ratings")
    ax.set_xlabel("Teacher Rating")
    ax.set_ylabel("Number of Instructors")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/01_instructor_rating_distribution.png", dpi=150)
    plt.close(fig)

    print("Q1. Instructor rating distribution")
    print(f"    mean={teachers['TeacherRating'].mean():.2f}  "
          f"median={teachers['TeacherRating'].median():.2f}  "
          f"std={teachers['TeacherRating'].std():.2f}")


def q2_experience_vs_rating(teachers, course_summary):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    sns.regplot(
        data=teachers, x="YearsOfExperience", y="TeacherRating",
        ax=axes[0], scatter_kws={"alpha": 0.5}, line_kws={"color": "red"},
    )
    axes[0].set_title("Experience vs Teacher Rating")

    sns.regplot(
        data=course_summary, x="YearsOfExperience", y="CourseRating",
        ax=axes[1], scatter_kws={"alpha": 0.3}, line_kws={"color": "red"},
    )
    axes[1].set_title("Experience vs Course Rating")

    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/02_experience_vs_rating.png", dpi=150)
    plt.close(fig)

    r_teacher, p_teacher = stats.pearsonr(teachers["YearsOfExperience"], teachers["TeacherRating"])
    r_course, p_course = stats.pearsonr(course_summary["YearsOfExperience"], course_summary["CourseRating"])

    print("\nQ2. Experience vs performance")
    print(f"    corr(Experience, TeacherRating) = {r_teacher:.2f}  (p={p_teacher:.4f})")
    print(f"    corr(Experience, CourseRating)  = {r_course:.2f}  (p={p_course:.4f})")


def q3_teacher_vs_course_rating(course_summary):
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.scatterplot(
        data=course_summary, x="TeacherRating", y="CourseRating",
        alpha=0.4, ax=ax, color="#55A868",
    )
    sns.regplot(
        data=course_summary, x="TeacherRating", y="CourseRating",
        scatter=False, ax=ax, color="red",
    )
    ax.set_title("Teacher Rating vs Course Rating")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/03_teacher_vs_course_rating.png", dpi=150)
    plt.close(fig)

    r, p = stats.pearsonr(course_summary["TeacherRating"], course_summary["CourseRating"])
    print("\nQ3. Teacher rating vs course rating")
    print(f"    corr = {r:.2f}  (p={p:.4f})")


def q4_expertise_performance(course_summary):
    expertise_summary = (
        course_summary.groupby("Expertise")["CourseRating"]
        .agg(["mean", "std", "count"])
        .sort_values("mean", ascending=False)
        .round(2)
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        x=expertise_summary["mean"], y=expertise_summary.index,
        ax=ax, color="#8172B2",
    )
    ax.set_title("Average Course Rating by Instructor Expertise")
    ax.set_xlabel("Average Course Rating")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/04_expertise_performance.png", dpi=150)
    plt.close(fig)

    print("\nQ4. Expertise areas ranked by average course rating")
    print(expertise_summary.to_string())


def q5_rating_tier_vs_enrollment(course_summary):
    df = course_summary.copy()
    df["RatingTier"] = df["TeacherRating"].apply(rating_tier)

    tier_summary = (
        df.groupby("RatingTier")["EnrollmentCount"]
        .agg(["mean", "median", "count"])
        .reindex(["High", "Mid", "Low"])
        .round(1)
    )

    fig, ax = plt.subplots(figsize=(7, 5))
    order = ["Low", "Mid", "High"]
    sns.boxplot(data=df, x="RatingTier", y="EnrollmentCount", order=order, hue="RatingTier",
                legend=False, palette="Set2", ax=ax)
    ax.set_title("Enrollment Volume by Instructor Rating Tier")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/05_rating_tier_vs_enrollment.png", dpi=150)
    plt.close(fig)

    print("\nQ5. Enrollment by instructor rating tier")
    print(tier_summary.to_string())


def category_level_heatmap(course_summary):
    pivot = course_summary.pivot_table(
        index="CourseCategory", columns="CourseLevel", values="CourseRating", aggfunc="mean"
    ).round(2)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(pivot, annot=True, cmap="YlGnBu", ax=ax, cbar_kws={"label": "Avg Course Rating"})
    ax.set_title("Course Rating Heatmap: Category vs Level")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/06_category_level_heatmap.png", dpi=150)
    plt.close(fig)


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    teachers, courses, transactions, enrollments, course_summary = build_master_table()

    print("=" * 60)
    print("EDUPRO INSTRUCTOR & COURSE QUALITY -- EDA SUMMARY")
    print("=" * 60)

    q1_instructor_rating_distribution(teachers)
    q2_experience_vs_rating(teachers, course_summary)
    q3_teacher_vs_course_rating(course_summary)
    q4_expertise_performance(course_summary)
    q5_rating_tier_vs_enrollment(course_summary)
    category_level_heatmap(course_summary)

    kpis = compute_kpis(teachers, courses, course_summary)
    print("\n" + "=" * 60)
    print("KPI SUMMARY")
    print("=" * 60)
    for name, value in kpis.items():
        print(f"    {name:<30} {value}")

    print(f"\nCharts saved to ./{OUT_DIR}/")


if __name__ == "__main__":
    main()
