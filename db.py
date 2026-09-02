import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'autograder.db')

def get_db_connection():
    """Returns a SQLite connection with dict-like row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates tables and populates sample data if not present."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('teacher', 'student')),
            name TEXT NOT NULL
        )
    ''')

    # Create Questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            reference_answer TEXT NOT NULL,
            max_marks REAL NOT NULL DEFAULT 10.0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    # Create Submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            student_answer TEXT NOT NULL,
            similarity_score REAL NOT NULL,
            marks_obtained REAL NOT NULL,
            max_marks REAL NOT NULL,
            feedback TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    ''')

    # Insert default sample users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('teacher', 'teacher123', 'teacher', 'Prof. Alan Turing'),
            ('student', 'student123', 'student', 'John Doe'),
            ('student2', 'student123', 'student', 'Jane Smith')
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
            sample_users
        )
        conn.commit()

    # Insert default sample questions if empty
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        # Get teacher id
        cursor.execute("SELECT id FROM users WHERE username='teacher'")
        teacher = cursor.fetchone()
        teacher_id = teacher['id'] if teacher else 1

        sample_questions = [
            (
                "What is Machine Learning and what are its primary paradigms?",
                "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. Its primary paradigms include supervised learning where models learn from labeled data, unsupervised learning which discovers hidden patterns in unlabeled data, and reinforcement learning where agents learn through trial and error rewards.",
                10.0,
                teacher_id
            ),
            (
                "Explain the concept of Virtual Memory in Operating Systems.",
                "Virtual memory is a memory management technique that creates an illusion to users of having a very large main memory. It allows the execution of processes that may not be completely in physical RAM by using secondary storage like hard disk as an extension of RAM using paging and segmentation techniques.",
                10.0,
                teacher_id
            ),
            (
                "What is Normalization in Database Management Systems (DBMS)?",
                "Normalization is the systematic process of organizing data in a relational database to reduce data redundancy and improve data integrity. It involves dividing large tables into smaller, well-structured tables and establishing relationships between them using normal forms like 1NF, 2NF, 3NF, and BCNF.",
                10.0,
                teacher_id
            ),
            (
                "Define Object-Oriented Programming (OOP) and its core pillars.",
                "Object-Oriented Programming is a programming paradigm based on the concept of objects containing data and code. The four core pillars of OOP are Encapsulation (bundling data and methods), Abstraction (hiding implementation details), Inheritance (reusing parent class properties), and Polymorphism (allowing one interface with multiple forms).",
                10.0,
                teacher_id
            )
        ]

        cursor.executemany(
            "INSERT INTO questions (question_text, reference_answer, max_marks, created_by) VALUES (?, ?, ?, ?)",
            sample_questions
        )
        conn.commit()

    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with sample users and questions.")
