import os
import logging
import json
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from langchain_groq import ChatGroq
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Initialize Groq client via LangChain
chat_model = ChatGroq(
    api_key="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",
    model_name="llama3-70b-8192"
)

# Define the response schema for quiz questions
response_schemas = [
    ResponseSchema(name="questions", description="Array of quiz questions", type="array")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Create a prompt template
prompt_template = """Generate {num_questions} multiple choice questions about {topic}.
Each question should have 4 options and include an explanation for the correct answer.

{format_instructions}

The questions array should contain objects with this structure:
{{
    "question": "question text",
    "options": ["option A", "option B", "option C", "option D"],
    "correct": "the correct option",
    "explanation": "detailed explanation for the answer"
}}"""

prompt = ChatPromptTemplate(
    messages=[
        HumanMessagePromptTemplate.from_template(prompt_template)
    ],
    input_variables=["topic", "num_questions"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        topic = request.form.get('topic')
        num_questions = int(request.form.get('num_questions', 5))

        try:
            # Generate questions using LangChain + Groq
            chain_input = {
                "topic": topic,
                "num_questions": num_questions
            }
            messages = prompt.format_messages(**chain_input)
            response = chat_model.invoke(messages)

            # Log the raw response for debugging
            logging.debug(f"Raw LangChain response: {response.content}")

            try:
                # Parse the structured output
                questions_data = output_parser.parse(response.content)

                # Store quiz data in session
                session['quiz_data'] = {'questions': questions_data['questions']}
                session['current_question'] = 0
                session['score'] = 0
                session['answers'] = []

                return redirect(url_for('quiz'))

            except Exception as parse_error:
                error_msg = f"Error parsing response: {str(parse_error)}"
                logging.error(error_msg)
                return render_template('generate.html', error=error_msg)

        except Exception as e:
            error_msg = f"Failed to generate quiz: {str(e)}"
            logging.error(error_msg)
            return render_template('generate.html', error=error_msg)

    return render_template('generate.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'quiz_data' not in session:
        return redirect(url_for('generate'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        session['answers'].append(answer)

        # Update score
        current_q = session['current_question']
        quiz_data = session['quiz_data']
        if answer == quiz_data['questions'][current_q]['correct']:
            session['score'] += 1

        session['current_question'] += 1

        if session['current_question'] >= len(quiz_data['questions']):
            return redirect(url_for('feedback'))

    return render_template('quiz.html', 
                         question=session['quiz_data']['questions'][session['current_question']],
                         question_num=session['current_question'] + 1,
                         total_questions=len(session['quiz_data']['questions']))

@app.route('/feedback')
def feedback():
    if 'quiz_data' not in session:
        return redirect(url_for('generate'))

    quiz_data = session['quiz_data']
    score = session['score']
    total = len(quiz_data['questions'])
    percentage = (score / total) * 100

    return render_template('feedback.html',
                         score=score,
                         total=total,
                         percentage=percentage,
                         questions=quiz_data['questions'],
                         answers=session['answers'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)