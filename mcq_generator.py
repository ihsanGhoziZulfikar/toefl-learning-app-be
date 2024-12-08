from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains import SequentialChain
import os
from dotenv import load_dotenv
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
print('GEMINI_API_KEY')
print(GEMINI_API_KEY)
llm = ChatGoogleGenerativeAI(api_key=GEMINI_API_KEY,model="gemini-pro",temperature=0.7)

TEMPLATE = """
You are an expert {subject} MCQ creator.It is your job to create a {subject} quiz of {number} multiple-choice questions suitable for TOEFL practice. Ensure that the questions test various aspects of {subject}. The tone should be {tone}. Make sure the questions are diverse, accurate, and conform to the {subject} rules in the text provided. Format your response like {response_json} below, and ensure to create exactly {number} {subject}-focused MCQs.
"""

# including sentence structure, verb tense, prepositions, conjunctions, and punctuation

quiz_generation_prompt = PromptTemplate(
    input_variables=["number", "subject", "tone", "response_json"],
    template=TEMPLATE
    )

quiz_chain=LLMChain(llm=llm, prompt=quiz_generation_prompt, output_key="quiz", verbose=True)

generate_evaluate_chain=SequentialChain(chains=[quiz_chain], 
        input_variables=["number", "subject", "tone", "response_json"], verbose=True)