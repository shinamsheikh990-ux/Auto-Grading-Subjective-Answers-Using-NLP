import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure required NLTK resources are available
def ensure_nltk_resources():
    packages = ['punkt', 'punkt_tab', 'stopwords', 'wordnet', 'omw-1.4']
    for pkg in packages:
        try:
            nltk.download(pkg, quiet=True)
        except Exception as e:
            print(f"Notice: NLTK package {pkg} could not be downloaded ({e}). Using built-in fallbacks.")

ensure_nltk_resources()

# Initialize NLP components
try:
    STOP_WORDS = set(stopwords.words('english'))
except Exception:
    STOP_WORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
        'you\'ll', "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
        'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
        'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
        'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a',
        'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
        'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
        'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now'
    }

stemmer = PorterStemmer()
try:
    lemmatizer = WordNetLemmatizer()
    lemmatizer.lemmatize("testing")
except Exception:
    lemmatizer = None


def preprocess_text(text):
    """
    Cleans and preprocesses input text:
    1. Lowercases text
    2. Removes punctuation and special symbols
    3. Tokenizes into words
    4. Removes common English stopwords
    5. Lemmatizes and stems words to their base root forms
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Lowercase
    text = text.lower().strip()

    # 2. Remove punctuation / special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    # 3. Tokenize
    try:
        tokens = nltk.word_tokenize(text)
    except Exception:
        tokens = text.split()

    # 4. Filter stopwords and single-character noise
    filtered_tokens = [
        token for token in tokens
        if token not in STOP_WORDS and len(token) > 1
    ]

    # 5. Lemmatization & Stemming
    processed_tokens = []
    for token in filtered_tokens:
        word = token
        if lemmatizer:
            try:
                word = lemmatizer.lemmatize(word)
            except Exception:
                pass
        try:
            word = stemmer.stem(word)
        except Exception:
            pass
        processed_tokens.append(word)

    return " ".join(processed_tokens)


def extract_keywords_display(text):
    """Extracts readable normalized keywords for UI display."""
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return sorted(list(set(w for w in words if w not in STOP_WORDS)))


def grade_answer(reference_answer, student_answer, max_marks=10):
    """
    Grades a subjective answer against a model reference answer using:
    - Text Preprocessing & Stemming
    - TF-IDF Vectorization
    - Cosine Similarity
    - Formula: marks = similarity_score * max_marks
    """
    max_marks = float(max_marks) if max_marks else 10.0
    
    clean_ref = preprocess_text(reference_answer)
    clean_student = preprocess_text(student_answer)

    # If student answer is completely empty or has no content
    if not clean_student:
        return {
            'similarity_score': 0.0,
            'similarity_percentage': 0.0,
            'marks_obtained': 0.0,
            'max_marks': max_marks,
            'feedback': "No substantive answer provided or only stopwords/punctuation detected.",
            'matched_keywords': [],
            'missing_keywords': extract_keywords_display(reference_answer),
            'clean_reference': clean_ref,
            'clean_student': clean_student
        }

    # If reference answer is empty
    if not clean_ref:
        return {
            'similarity_score': 0.0,
            'similarity_percentage': 0.0,
            'marks_obtained': 0.0,
            'max_marks': max_marks,
            'feedback': "Reference answer is not properly set by the teacher.",
            'matched_keywords': [],
            'missing_keywords': [],
            'clean_reference': clean_ref,
            'clean_student': clean_student
        }

    # TF-IDF Vectorization and Cosine Similarity
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([clean_ref, clean_student])
        
        # Calculate Cosine Similarity
        cos_sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        raw_similarity = float(cos_sim_matrix[0][0])
        
        # Clamp similarity between 0.0 and 1.0
        similarity_score = max(0.0, min(1.0, raw_similarity))
    except Exception as e:
        print(f"Error during vectorization: {e}")
        similarity_score = 0.0

    # Calculate final marks
    marks_obtained = round(similarity_score * max_marks, 2)
    similarity_percentage = round(similarity_score * 100, 2)

    # Keyword match analysis for educational feedback
    ref_display_words = set(extract_keywords_display(reference_answer))
    student_display_words = set(extract_keywords_display(student_answer))
    
    # Also check stemmed overlaps
    ref_stem_map = {stemmer.stem(w): w for w in ref_display_words}
    student_stems = {stemmer.stem(w) for w in student_display_words}
    
    matched_stems = set(ref_stem_map.keys()).intersection(student_stems)
    matched_keywords = sorted([ref_stem_map[s] for s in matched_stems])
    missing_keywords = sorted([ref_stem_map[s] for s in ref_stem_map if s not in matched_stems])

    # Generate constructive feedback
    if similarity_percentage >= 85:
        feedback = "Outstanding! Your answer is comprehensive, accurate, and closely aligns with the reference answer."
    elif similarity_percentage >= 70:
        feedback = "Very Good! You covered most core concepts and key terminology well."
    elif similarity_percentage >= 50:
        feedback = "Good attempt! You addressed several key points, but some details and concepts are missing."
    elif similarity_percentage >= 30:
        feedback = "Partially relevant. Your answer touches on the subject, but lacks key technical concepts."
    else:
        feedback = "Needs improvement. Your answer does not sufficiently cover the expected key concepts."

    return {
        'similarity_score': round(similarity_score, 4),
        'similarity_percentage': similarity_percentage,
        'marks_obtained': marks_obtained,
        'max_marks': max_marks,
        'feedback': feedback,
        'matched_keywords': matched_keywords,
        'missing_keywords': missing_keywords,
        'clean_reference': clean_ref,
        'clean_student': clean_student
    }
