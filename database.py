from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = "mysql+mysqlconnector://root:@localhost/english_app"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text, nullable=False)
    questions = relationship("Question", back_populates="article")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(String(255), nullable=False)
    cefr_level = Column(String(50), nullable=False)
    article = relationship("Article", back_populates="questions")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    cefr_results = relationship("CEFRResult", back_populates="user")

class CEFRResult(Base):
    __tablename__ = "cefr_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text = Column(Text, nullable=False)
    predicted_level = Column(String(50), nullable=False)
    user = relationship("User", back_populates="cefr_results")

def init_db():
    Base.metadata.create_all(bind=engine)
