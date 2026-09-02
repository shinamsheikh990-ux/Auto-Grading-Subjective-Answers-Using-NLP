import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_db_connection, init_db
from nlp_grader import grade_answer

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database on startup
with app.app_context():
    init_db()

# Decorators for route protection
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'teacher':
            flash('Access denied. Teacher privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            flash('Access denied. Student privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------- AUTHENTICATION ROUTES ----------------------

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()

        if not username or not password or not role:
            flash('Please fill in all fields and select your role.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ? AND role = ?',
            (username, password, role)
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            flash(f"Welcome back, {user['name']}!", 'success')
            if user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username, password, or role selection.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()

        if not name or not username or not password or not role:
            flash('Please complete all registration fields.', 'danger')
            return render_template('register.html')

        if role not in ['teacher', 'student']:
            flash('Invalid role selected.', 'danger')
            return render_template('register.html')

        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            conn.close()
            flash('Username is already taken. Please choose another.', 'warning')
            return render_template('register.html')

        conn.execute(
            'INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)',
            (username, password, role, name)
        )
        conn.commit()
        conn.close()

        flash('Registration successful! Please log in with your credentials.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ---------------------- TEACHER ROUTES ----------------------

@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    conn = get_db_connection()
    questions = conn.execute(
        '''
        SELECT q.*, u.name as author_name,
               (SELECT COUNT(*) FROM submissions s WHERE s.question_id = q.id) as submission_count,
               (SELECT AVG(s.marks_obtained) FROM submissions s WHERE s.question_id = q.id) as avg_marks
        FROM questions q
        LEFT JOIN users u ON q.created_by = u.id
        ORDER BY q.id DESC
        '''
    ).fetchall()

    total_submissions = conn.execute('SELECT COUNT(*) FROM submissions').fetchone()[0]
    avg_score = conn.execute('SELECT AVG(similarity_score) FROM submissions').fetchone()[0] or 0.0
    conn.close()

    stats = {
        'total_questions': len(questions),
        'total_submissions': total_submissions,
        'avg_similarity': round(avg_score * 100, 1)
    }

    return render_template('teacher_dashboard.html', questions=questions, stats=stats)


@app.route('/teacher/add-question', methods=['GET', 'POST'])
@teacher_required
def add_question():
    if request.method == 'POST':
        question_text = request.form.get('question_text', '').strip()
        reference_answer = request.form.get('reference_answer', '').strip()
        max_marks = request.form.get('max_marks', '10').strip()

        if not question_text or not reference_answer:
            flash('Question text and model/reference answer are required.', 'danger')
            return render_template('add_question.html')

        try:
            max_marks_float = float(max_marks)
            if max_marks_float <= 0:
                raise ValueError()
        except ValueError:
            flash('Maximum marks must be a positive number.', 'danger')
            return render_template('add_question.html')

        conn = get_db_connection()
        conn.execute(
            '''
            INSERT INTO questions (question_text, reference_answer, max_marks, created_by)
            VALUES (?, ?, ?, ?)
            ''',
            (question_text, reference_answer, max_marks_float, session['user_id'])
        )
        conn.commit()
        conn.close()

        flash('Question saved successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('add_question.html')


@app.route('/teacher/delete-question/<int:question_id>', methods=['POST'])
@teacher_required
def delete_question(question_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM submissions WHERE question_id = ?', (question_id,))
    conn.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()
    flash('Question and associated submissions deleted successfully.', 'info')
    return redirect(url_for('teacher_dashboard'))


@app.route('/teacher/submissions')
@teacher_required
def teacher_submissions():
    conn = get_db_connection()
    submissions = conn.execute(
        '''
        SELECT s.*, q.question_text, q.reference_answer, u.name as student_name, u.username as student_username
        FROM submissions s
        JOIN questions q ON s.question_id = q.id
        JOIN users u ON s.student_id = u.id
        ORDER BY s.submitted_at DESC
        '''
    ).fetchall()
    conn.close()
    return render_template('teacher_submissions.html', submissions=submissions)


# ---------------------- STUDENT ROUTES ----------------------

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    conn = get_db_connection()
    student_id = session['user_id']

    # Fetch all questions and check if current student has submitted
    questions = conn.execute(
        '''
        SELECT q.*, 
               (SELECT COUNT(*) FROM submissions s WHERE s.question_id = q.id AND s.student_id = ?) as has_attempted,
               (SELECT s.marks_obtained FROM submissions s WHERE s.question_id = q.id AND s.student_id = ? ORDER BY s.id DESC LIMIT 1) as latest_marks
        FROM questions q
        ORDER BY q.id ASC
        ''',
        (student_id, student_id)
    ).fetchall()

    # Fetch student's submissions history
    history = conn.execute(
        '''
        SELECT s.*, q.question_text
        FROM submissions s
        JOIN questions q ON s.question_id = q.id
        WHERE s.student_id = ?
        ORDER BY s.submitted_at DESC
        ''',
        (student_id,)
    ).fetchall()

    conn.close()
    return render_template('student_dashboard.html', questions=questions, history=history)


@app.route('/student/attempt/<int:question_id>', methods=['GET', 'POST'])
@student_required
def attempt_question(question_id):
    conn = get_db_connection()
    question = conn.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()

    if not question:
        conn.close()
        flash('Question not found.', 'danger')
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        student_answer = request.form.get('student_answer', '').strip()

        if not student_answer:
            conn.close()
            flash('Please enter your subjective answer before submitting.', 'warning')
            return render_template('answer_question.html', question=question)

        # Grade answer using NLP Engine
        grade_result = grade_answer(
            reference_answer=question['reference_answer'],
            student_answer=student_answer,
            max_marks=question['max_marks']
        )

        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO submissions (
                question_id, student_id, student_answer, 
                similarity_score, marks_obtained, max_marks, feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                question_id,
                session['user_id'],
                student_answer,
                grade_result['similarity_score'],
                grade_result['marks_obtained'],
                grade_result['max_marks'],
                grade_result['feedback']
            )
        )
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()

        flash('Your answer has been evaluated and graded successfully!', 'success')
        return redirect(url_for('view_result', submission_id=submission_id))

    conn.close()
    return render_template('answer_question.html', question=question)


@app.route('/student/result/<int:submission_id>')
@login_required
def view_result(submission_id):
    conn = get_db_connection()
    submission = conn.execute(
        '''
        SELECT s.*, q.question_text, q.reference_answer, u.name as student_name
        FROM submissions s
        JOIN questions q ON s.question_id = q.id
        JOIN users u ON s.student_id = u.id
        WHERE s.id = ?
        ''',
        (submission_id,)
    ).fetchone()
    conn.close()

    if not submission:
        flash('Submission record not found.', 'danger')
        return redirect(url_for('index'))

    # Security check: Students can only view their own results, teachers can view all
    if session.get('role') == 'student' and submission['student_id'] != session['user_id']:
        flash('Access unauthorized.', 'danger')
        return redirect(url_for('student_dashboard'))

    # Recalculate keyword breakdown for enhanced visual feedback
    grade_info = grade_answer(
        reference_answer=submission['reference_answer'],
        student_answer=submission['student_answer'],
        max_marks=submission['max_marks']
    )

    similarity_percentage = round(submission['similarity_score'] * 100, 1)

    return render_template(
        'result.html',
        submission=submission,
        grade_info=grade_info,
        similarity_percentage=similarity_percentage
    )


if __name__ == '__main__':
    # Run the application
    print("Auto-Grading Subjective Answers NLP Server running at http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
