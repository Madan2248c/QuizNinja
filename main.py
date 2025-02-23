import os
import logging
import json
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        topic = request.form.get('topic')
        num_questions = int(request.form.get('num_questions', 5))

        try:
            # Generate questions using Groq API
            prompt = f"""Generate {num_questions} multiple choice questions about {topic}. 
            Format as JSON array with structure:
            {{
                "questions": [
                    {{
                        "question": "question text",
                        "options": ["A", "B", "C", "D"],
                        "correct": "correct option",
                        "explanation": "explanation for the answer"
                    }}
                ]
            }}"""

            completion = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )

            # Log the raw response for debugging
            response_content = completion.choices[0].message.content
            logging.debug(f"Raw Groq response: {response_content}")

            # Parse the JSON response before storing in session
            try:
                questions_data = json.loads(response_content)

                # Validate the response structure
                if 'questions' not in questions_data:
                    raise ValueError("Response missing 'questions' array")
                if not isinstance(questions_data['questions'], list):
                    raise ValueError("'questions' is not an array")
                if not questions_data['questions']:
                    raise ValueError("No questions were generated")

                session['quiz_data'] = questions_data
                session['current_question'] = 0
                session['score'] = 0
                session['answers'] = []

                return redirect(url_for('quiz'))

            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON format in response: {str(e)}"
                logging.error(error_msg)
                return render_template('generate.html', error=error_msg)
            except ValueError as e:
                error_msg = f"Invalid response format: {str(e)}"
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