from flask import Flask, request, jsonify
import json
import os
from mcq_generator import generate_evaluate_chain
import uuid
from datetime import datetime
import ast

app = Flask(__name__)

@app.route('/generate_questions', methods=['GET'])
def generate_questions():
    """
    Endpoint to generate multiple-choice questions and answers
    """
    with open("response.json",'r') as f:
        response_json = json.load(f)

    api_response = generate_evaluate_chain.invoke({
        "number": 2,
        "subject": 'grammar',
        "tone": 'conversational',
        "response_json": response_json
    })

    print('api_response')
    print(api_response)

    try:
        # quiz = json.loads(api_response["quiz"])
        quiz = ast.literal_eval(api_response["quiz"])  # Convert single-quoted string to Python dictionary
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse quiz data: {str(e)}"}), 500

    # Parse the response and restructure it
    questions = []
    for key, value in quiz.items():
        question = {
            "id": str(uuid.uuid4()),
            "question": value["mcq"],
            "choices": [{"a": value["options"]["a"]}, {"b": value["options"]["b"]},
                        {"c": value["options"]["c"]}, {"d": value["options"]["d"]}],
            "answer": value["correct"],
            "created_at": datetime.utcnow().isoformat()
        }
        questions.append(question)

    # Save the result to a JSON file
    output_file = 'Generated/questions.json'
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            existing_questions = json.load(f)
    else:
        existing_questions = {"questions": []}

    # Append the new questions
    existing_questions["questions"].extend(questions)

    with open(output_file, 'w') as f:
        json.dump(existing_questions, f, indent=4)

    return jsonify({
        "message": "Questions generated and appended successfully",
        "output_file": output_file,
        "data": questions
    })

@app.route('/get_questions', methods=['GET'])
def get_questions():
    """
    Endpoint to retrieve the generated questions from the JSON file.
    """
    output_file = 'Generated/questions.json'
    if not os.path.exists(output_file):
        return jsonify({"error": "No questions file found. Generate questions first."}), 404

    with open(output_file, 'r') as f:
        questions_data = json.load(f)

    return jsonify(questions_data)

if __name__ == '__main__':
    app.run(debug=True)
