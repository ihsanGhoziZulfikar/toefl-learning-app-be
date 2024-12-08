from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains import SequentialChain
import os
from dotenv import load_dotenv
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
llm = ChatGoogleGenerativeAI(api_key=GEMINI_API_KEY,model="gemini-pro",temperature=0.7)

TEMPLATE = """
You are an expert {subject} MCQ creator. Your task is to create a {subject} quiz with {number} multiple-choice questions, suitable for TOEFL practice. Ensure that the questions align with the {cefr_level} proficiency level and are tailored to the learner's interest in {interest}. 

The tone of the quiz should be {tone}. Make sure the questions test various aspects of {subject} in a diverse and accurate manner, adhering to {subject} rules. 

In addition to the quiz, for each question, provide a detailed explanation of why the correct answer is right and why the incorrect options are wrong. These explanations should serve as a discussion for learners who select the wrong answers.

Format your response in the structure of {response_json}, and ensure to create exactly {number} well-crafted, {subject}-focused MCQs along with discussions.
"""

quiz_generation_prompt = PromptTemplate(
    input_variables=["number", "cefr_level", "interest", "subject", "tone", "response_json"],
    template=TEMPLATE
    )

quiz_chain=LLMChain(llm=llm, prompt=quiz_generation_prompt, output_key="quiz", verbose=True)

generate_evaluate_chain=SequentialChain(chains=[quiz_chain], 
        input_variables=["number", "cefr_level", "interest", "subject", "tone", "response_json"], verbose=True)