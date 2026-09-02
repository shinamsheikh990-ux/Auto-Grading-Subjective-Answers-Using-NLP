import unittest
from nlp_grader import preprocess_text, grade_answer
from db import get_db_connection, init_db
from app import app

class AutoGraderTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()
        init_db()

    def test_nlp_preprocessing(self):
        sample_text = "The machine learning models are learning from data!"
        preprocessed = preprocess_text(sample_text)
        self.assertNotIn("the", preprocessed.split())
        self.assertNotIn("are", preprocessed.split())
        self.assertNotIn("from", preprocessed.split())
        self.assertIn("machin", preprocessed) # stemmed
        self.assertIn("learn", preprocessed)  # lemmatized & stemmed
        self.assertIn("data", preprocessed)

    def test_grading_identical_answer(self):
        ref = "Machine learning is a subset of artificial intelligence."
        student = "Machine learning is a subset of artificial intelligence."
        result = grade_answer(ref, student, max_marks=10)
        self.assertAlmostEqual(result['similarity_score'], 1.0, places=2)
        self.assertAlmostEqual(result['marks_obtained'], 10.0, places=1)
        self.assertEqual(result['similarity_percentage'], 100.0)

    def test_grading_paraphrased_answer(self):
        ref = "Virtual memory allows the execution of processes using paging and segmentation techniques."
        student = "Virtual memory executes processes with paging and segmentation."
        result = grade_answer(ref, student, max_marks=10)
        self.assertGreater(result['similarity_score'], 0.6)
        self.assertGreater(result['marks_obtained'], 6.0)

    def test_grading_irrelevant_answer(self):
        ref = "Object-Oriented Programming uses classes, inheritance, polymorphism, and encapsulation."
        student = "Photosynthesis is the process by which plants convert sunlight into chemical energy."
        result = grade_answer(ref, student, max_marks=10)
        self.assertLess(result['similarity_score'], 0.2)
        self.assertLess(result['marks_obtained'], 2.0)

    def test_grading_empty_answer(self):
        ref = "Database normalization reduces redundancy."
        student = ""
        result = grade_answer(ref, student, max_marks=10)
        self.assertEqual(result['similarity_score'], 0.0)
        self.assertEqual(result['marks_obtained'], 0.0)

    def test_db_content(self):
        conn = get_db_connection()
        teacher = conn.execute("SELECT * FROM users WHERE username='teacher'").fetchone()
        self.assertIsNotNone(teacher)
        self.assertEqual(teacher['role'], 'teacher')

        questions = conn.execute("SELECT * FROM questions").fetchall()
        self.assertGreaterEqual(len(questions), 4)
        conn.close()

    def test_login_and_student_flow(self):
        # 1. Login as student
        res = self.client.post('/login', data={
            'username': 'student',
            'password': 'student123',
            'role': 'student'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Student Dashboard', res.data)

        # 2. Attempt question #1
        answer_text = "Machine learning is part of artificial intelligence where models learn from data."
        submit_res = self.client.post('/student/attempt/1', data={
            'student_answer': answer_text
        }, follow_redirects=True)
        self.assertEqual(submit_res.status_code, 200)
        self.assertIn(b'Evaluation & Grading Report', submit_res.data)
        self.assertIn(b'NLP Cosine Similarity', submit_res.data)
        self.assertIn(b'Marks Obtained', submit_res.data)

    def test_teacher_add_question_flow(self):
        # 1. Login as teacher
        self.client.post('/login', data={
            'username': 'teacher',
            'password': 'teacher123',
            'role': 'teacher'
        }, follow_redirects=True)

        # 2. Add question
        res = self.client.post('/teacher/add-question', data={
            'question_text': 'What is recursion in programming?',
            'reference_answer': 'Recursion is a programming technique where a function calls itself directly or indirectly to solve smaller subproblems until a base condition is met.',
            'max_marks': '10'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Teacher Dashboard', res.data)
        self.assertIn(b'What is recursion in programming?', res.data)

if __name__ == '__main__':
    unittest.main()
