# Instructor Performance and Course Quality Evaluation — EduPro

Data analytics project for Unified Mentor Pvt. Ltd.: evaluates instructor
effectiveness and course quality on the EduPro platform using the
Teachers / Courses / Transactions dataset.

## Project structure

```
edupro_project/
├── data/
│   └── EduPro_Dataset.xlsx      # 3 sheets: Teachers, Courses, Transactions
├── outputs/                     # charts saved by data_analysis.py
├── data_pipeline.py             # loading, joins, KPI calculations (shared)
├── generate_sample_data.py      # creates a synthetic dataset for testing
├── data_analysis.py             # offline EDA -> answers + charts for the paper
├── app.py                       # Streamlit dashboard
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Using your real dataset

Drop the actual EduPro export at `data/EduPro_Dataset.xlsx` with exactly
these three sheets and column names (this matches the project brief):

- **Teachers**: TeacherID, TeacherName, Age, Gender, Expertise,
  YearsOfExperience, TeacherRating
- **Courses**: CourseID, CourseName, CourseCategory, CourseLevel,
  CourseRating
- **Transactions**: TransactionID, CourseID, TeacherID

`data_pipeline.py` reconstructs the course→instructor link from
`Transactions` (the most frequent teacher associated with a course, since
`Courses` itself doesn't carry `TeacherID`), so no other code needs to
change once real data is in place.

If you don't have the real file yet, generate a synthetic one to develop
and demo against:

```bash
python generate_sample_data.py
```

## Run the EDA / research-paper script

Answers each analytical question from the brief and saves charts to
`outputs/`:

```bash
python data_analysis.py
```

## Run the dashboard

```bash
streamlit run app.py
```

Dashboard modules:
- Instructor performance leaderboard
- Experience vs rating scatter plots (with trendlines)
- Course quality heatmap (category × level)
- Expertise-wise performance comparison

Filters: instructor expertise, course category, course level, rating range
— all in the sidebar, applied live across every tab.

## KPIs computed

| KPI | Meaning |
|---|---|
| Average Teacher Rating | Overall teaching quality benchmark |
| Average Course Rating | Overall content effectiveness |
| Rating Consistency Index | How consistent each instructor's ratings are across their own courses |
| Experience Impact Score | Correlation between tenure and rating, rescaled 0–100 |
| Enrollment Influence Ratio | Avg enrollments for high-rated vs low-rated instructors |
