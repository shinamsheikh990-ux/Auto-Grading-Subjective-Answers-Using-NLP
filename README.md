# 📝 Auto-Grading Subjective Answers Using NLP

A beginner-friendly, fully functional web application built with **Flask**, **SQLite**, **NLTK**, and **Scikit-learn** that automatically evaluates and grades subjective (descriptive) student answers against a teacher's reference answer using Natural Language Processing (NLP), TF-IDF Vectorization, and Cosine Similarity.

---

## 🌟 Key Features

### 👨‍🏫 Teacher Role
- **Login & Registration**: Dedicated role-based authentication.
- **Create Questions**: Enter subjective questions, comprehensive model/reference answers, and assign maximum marks.
- **Question Management**: View, track, and delete created questions.
- **Evaluation Overview**: View all student submissions, calculated marks, cosine similarity percentages, and automated feedback.

### 🎓 Student Role
- **Login & Registration**: Dedicated student access.
- **Browse Questions**: View all available questions set by teachers.
- **Subjective Answer Submission**: Comfortable writing environment with live word count.
- **Instant NLP Grading Result**: Real-time evaluation report displaying:
  - Question prompt
  - Student's submitted answer
  - Teacher's reference answer
  - Similarity percentage (with dynamic visual progress bar)
  - Marks obtained vs Maximum marks
  - Tailored constructive feedback
  - Matched and missing key concepts analysis

---

## 🔬 NLP & Grading Methodology

The evaluation pipeline follows a transparent, robust, and interpretable process:

```
[Student Answer] ──> [Preprocess: Lowercase, Punctuation, Stopwords, Lemmatize] ──┐
                                                                                   ├──> [TF-IDF Vectorizer] ──> [Cosine Similarity] ──> [Marks Formula]
[Reference Answer] ─> [Preprocess: Lowercase, Punctuation, Stopwords, Lemmatize] ──┘
```

1. **Preprocessing (NLTK)**:
   - Lowercasing and punctuation removal.
   - Word tokenization.
   - English stopword removal (e.g., 'is', 'the', 'and').
   - Lemmatization (using WordNet) to convert words to base dictionary forms (e.g., *learning* $\to$ *learn*).

2. **Feature Extraction (Scikit-learn)**:
   - Convert preprocessed texts into Term Frequency-Inverse Document Frequency (**TF-IDF**) vectors with unigram & bigram support.

3. **Cosine Similarity**:
   - Computes the angular cosine distance between the reference answer vector $\mathbf{A}$ and student answer vector $\mathbf{B}$:
     $$\text{Similarity}(\mathbf{A}, \mathbf{B}) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$

4. **Marks Calculation Formula**:
   $$\text{Obtained Marks} = \text{round}(\text{Similarity Score} \times \text{Maximum Marks}, 2)$$
   $$\text{Similarity Percentage} = \text{Similarity Score} \times 100\%$$

*Example:*
- **Similarity Score**: `0.80` ($80.0\%$)
- **Maximum Marks**: `10`
- **Final Marks**: `8.0 / 10`

---

## 📁 Project Structure

```
auto_grader_nlp/
├── app.py                  # Main Flask application & route controllers
├── nlp_grader.py           # NLP text preprocessing, TF-IDF vectorizer & cosine similarity
├── db.py                   # SQLite database configuration & sample data seeder
├── autograder.db           # SQLite database file (created automatically)
├── requirements.txt        # Python package dependencies
├── README.md               # Documentation and setup guide
├── static/
│   └── css/
│       └── style.css       # Clean, modern UI stylesheet
└── templates/
    ├── base.html           # Master layout with navbar and alerts
    ├── login.html          # Login page with 1-click demo logins
    ├── register.html       # Account registration
    ├── teacher_dashboard.html # Teacher dashboard & question list
    ├── add_question.html   # Form for adding questions and reference answers
    ├── teacher_submissions.html # Student submissions evaluation list
    ├── student_dashboard.html # Student dashboard & available questions
    ├── answer_question.html# Subjective answer entry page
    └── result.html         # Detailed grading result and keyword breakdown
```

---

## 🚀 Getting Started & Running the App

### 1. Prerequisites
Ensure you have **Python 3.8+** installed.

### 2. Install Dependencies
Open your terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the Flask development server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Preloaded Sample Accounts & Data

The database comes pre-initialized with sample users and questions across Computer Science topics:

| Role | Username | Password | Full Name |
|---|---|---|---|
| **Teacher** | `teacher` | `teacher123` | Prof. Alan Turing |
| **Student** | `student` | `student123` | John Doe |
| **Student** | `student2` | `student123` | Jane Smith |

*Note: You can also use the **Quick Demo Login** buttons on the login screen for 1-click access, or register new accounts freely.*

---

## 🛠️ Technology Stack
- **Backend Framework**: Python Flask
- **NLP & Similarity**: NLTK, Scikit-learn (`TfidfVectorizer`, `cosine_similarity`)
- **Database**: SQLite3 (Embedded, zero setup required)
- **Frontend**: HTML5, CSS3, Jinja2 Templates
