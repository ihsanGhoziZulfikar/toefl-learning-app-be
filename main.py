from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import joblib
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from transformers import pipeline
from database import SessionLocal, init_db, Article, Question, User, CEFRResult

# Initialize database
init_db()

app = FastAPI()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ArticleCreate(BaseModel):
    title: str
    content: str

class ArticleID(BaseModel):
    article_id: int

class UserCreate(BaseModel):
    username: str
    password: str

class UserCEFRCheck(BaseModel):
    user_id: int
    text: str

# Load model and vectorizer
model = joblib.load("Logistic_Regression.joblib")
vectorizer = joblib.load("tfidf_vectorizer.joblib")

@app.post("/users/", response_model=UserCreate)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/articles/", response_model=ArticleCreate, tags=["Articles"])
async def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    db_article = Article(title=article.title, content=article.content)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@app.get("/articles/", response_model=List[ArticleCreate], tags=["Articles"])
async def read_articles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    articles = db.query(Article).offset(skip).limit(limit).all()
    return articles

class TextData(BaseModel):
    texts: List[str]

@app.get("/")
async def read_root():
    return {"message": "Welcome to the CEFR prediction API"}

@app.post("/predict/cefr-level", tags=["Prediction"])
async def predict_cefr(data: TextData):
    cleaned_texts = [clean_text(text) for text in data.texts]
    X_tfidf = vectorizer.transform(cleaned_texts)
    predictions = model.predict(X_tfidf)
    return {"predictions": predictions.tolist()}

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

nltk.download('punkt')

ner_pipeline = pipeline('ner', grouped_entities=True)

def get_named_entities(text):
    ner_results = ner_pipeline(text)
    entities = [result['word'] for result in ner_results]
    return entities

def generate_questions(article):
    sentences = sent_tokenize(article)
    word_tokens = word_tokenize(article)
    
    named_entities = get_named_entities(article)
    freq_dist = nltk.FreqDist(word_tokens)
    
    keyword_candidates = list(set(named_entities + [word for word, freq in freq_dist.most_common(20)]))
    
    keywords = []
    seen = set()
    for keyword in keyword_candidates:
        if keyword.lower() not in seen:
            keywords.append(keyword)
            seen.add(keyword.lower())
    
    questions = []
    used_sentences = set()
    used_keywords = set()

    for keyword in keywords:
        if keyword.lower() in used_keywords:
            continue

        for sentence in sentences:
            if keyword in sentence and sentence not in used_sentences:
                question = re.sub(r'\b' + re.escape(keyword) + r'\b', '_____', sentence, flags=re.IGNORECASE)
                if question != sentence:
                    used_keywords.add(keyword.lower())
                    used_sentences.add(sentence)
                    question_data = {
                        'question': question,
                        'answer': keyword
                    }
                    questions.append(question_data)
                    break
    
    return questions

@app.post("/generate/questions", tags=["Question Generation"])
async def question_generation(data: ArticleID, db: Session = Depends(get_db)):
    db_article = db.query(Article).filter(Article.id == data.article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")

    questions = generate_questions(db_article.content)
    cleaned_questions = [clean_text(q['question']) for q in questions]
    X_tfidf = vectorizer.transform(cleaned_questions)
    predictions = model.predict(X_tfidf)
    
    db_questions = []
    for i, question in enumerate(questions):
        db_question = Question(
            article_id=data.article_id,
            question=question['question'],
            answer=question['answer'],
            cefr_level=predictions[i]
        )
        db_questions.append(db_question)
        db.add(db_question)
    
    db.commit()
    
    return {"questions": [{"question": q.question, "answer": q.answer, "cefr_level": q.cefr_level} for q in db_questions]}

@app.post("/users/cefr-check", tags=["CEFR Check"])
async def user_cefr_check(data: UserCEFRCheck, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    cleaned_text = clean_text(data.text)
    X_tfidf = vectorizer.transform([cleaned_text])
    predicted_level = model.predict(X_tfidf)[0]
    
    cefr_result = CEFRResult(
        user_id=data.user_id,
        text=data.text,
        predicted_level=predicted_level
    )
    db.add(cefr_result)
    db.commit()
    db.refresh(cefr_result)
    
    return {"user_id": cefr_result.user_id, "text": cefr_result.text, "predicted_level": cefr_result.predicted_level}
