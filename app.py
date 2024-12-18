from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import threading
import uuid
import CardinalisAPI
import json
import os
from datetime import datetime

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = key

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Task model
class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    result = db.Column(db.Text, nullable=True)  # Store all flashcards as JSON
    status = db.Column(db.String(50), default="in progress")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize the database
with app.app_context():
    db.create_all()

api = CardinalisAPI.API(key)

def api_call(topic, level, user_id, task_id):
    with app.app_context():
        try:
            print(f"Starting API call for task_id: {task_id}, topic: {topic}, level: {level}")
            result = json.loads(api.flashcards(topic, level))
            print(f"API call successful for task_id: {task_id}, received terms: {result.get('terms', [])}")
            terms = result.get('terms', [])
            formatted_result = [
                {"front": card.get('term', ''), "back": card.get('answer', '')}
                for card in terms if isinstance(card, dict)
            ]
            task = db.session.query(Task).filter_by(id=task_id).first()
            task.result = json.dumps(formatted_result)
            task.status = "completed"
            db.session.commit()
            print(f"Task {task_id} completed successfully with {len(formatted_result)} flashcards.")
        except Exception as e:
            print(f"Error during API call for task_id: {task_id}, error: {e}")
            task = db.session.query(Task).filter_by(id=task_id).first()
            if task:
                task.status = "failed"
            db.session.commit()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        topic = request.form['topic']
        level = request.form['level']
        task_id = uuid.uuid4().hex
        user_id = request.cookies.get('user_id', str(uuid.uuid4()))

        print(f"New task created with task_id: {task_id}, topic: {topic}, level: {level}")
        new_task = Task(id=task_id, topic=topic, level=level)
        db.session.add(new_task)
        db.session.commit()

        threading.Thread(target=api_call, args=(topic, level, user_id, task_id)).start()
        return redirect(url_for('loading_cards', task_id=task_id))
    else:
        user_id = request.cookies.get('user_id', str(uuid.uuid4()))
        response = make_response(render_template('home.html'))
        response.set_cookie('user_id', user_id, max_age=60*60*24*30*12)
        return response

@app.route('/loading_cards', methods=['GET'])
def loading_cards():
    task_id = request.args.get('task_id')
    print(f"Loading page accessed for task_id: {task_id}")
    return render_template('generation.html', task_id=task_id)

@app.route('/check_status', methods=['GET'])
def check_status():
    task_id = request.args.get('task_id')
    print(f"Checking status for task_id: {task_id}")
    task = db.session.query(Task).filter_by(id=task_id).first()
    if not task:
        print(f"Task {task_id} not found.")
        return jsonify({'status': 'unknown', 'result': None})

    print(f"Task {task_id} status: {task.status}")
    if task.status == "completed":
        result = json.loads(task.result) if task.result else []
        print(f"Task {task_id} completed. Returning results.")
        return jsonify({"status": task.status, "result": result})

    return jsonify({"status": task.status, "result": None})

@app.route('/show_result', methods=['GET'])
def show_result():
    task_id = request.args.get('task_id')
    print(f"Displaying results for task_id: {task_id}")
    task = db.session.query(Task).filter_by(id=task_id).first()
    if not task or not task.result:
        print(f"No results found for task_id: {task_id}")
        return redirect(url_for('home'))

    formatted_flashcards = json.loads(task.result)

    replacment_ready_flashcards = "["

    for i in formatted_flashcards:
        replacment_ready_flashcards = replacment_ready_flashcards + '{front: "front_term", back: "back_defenition",}'.replace("back_defenition", i['back']).replace("front_term", i['front'])
    replacment_ready_flashcards = replacment_ready_flashcards[:-1]
    replacment_ready_flashcards = replacment_ready_flashcards + "]"
    print()
    return render_template('result.html', placeholder=formatted_flashcards)

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True)
