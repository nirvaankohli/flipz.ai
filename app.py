from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response
import threading
import uuid
import CardinalisAPI
import json
import os
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = key

# Thread-safe storage for task statuses
tasks = defaultdict(dict)
lock = threading.Lock()

api = CardinalisAPI.API(key)

def api_call(topic, level, user_id, task_id):
    try:
        with lock:
            tasks[user_id][task_id] = {'status': 'in progress', 'result': None}

        # Simulate API call
        result = api.flashcards(topic, level)
        
        with lock:
            tasks[user_id][task_id] = {'status': 'completed', 'result': result}
    except Exception as e:
        with lock:
            tasks[user_id][task_id] = {'status': 'failed', 'result': str(e)}

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        topic = request.form['topic']
        level = request.form['level']
        user_id = request.cookies.get('user_id') or str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Start the API call in a background thread
        threading.Thread(target=api_call, args=(topic, level, user_id, task_id)).start()

        return redirect(url_for('loading_cards', task_id=task_id))
    else:
        user_id = request.cookies.get('user_id') or str(uuid.uuid4())
        response = make_response(render_template('home.html'))
        response.set_cookie('user_id', user_id, max_age=60*60*24*30*12)
        return response

@app.route('/loading_cards', methods=['GET'])
def loading_cards():
    task_id = request.args.get('task_id')
    return render_template('generation.html', task_id=task_id)

@app.route('/check_status', methods=['GET'])
def check_status():
    user_id = request.cookies.get('user_id')
    task_id = request.args.get('task_id')

    with lock:
        task_info = tasks.get(user_id, {}).get(task_id)

    if task_info:
        return jsonify(task_info)
    else:
        return jsonify({"status": "unknown", "result": None}), 404

@app.route('/show_result', methods=['GET'])
def show_result():
    user_id = request.cookies.get('user_id')
    task_id = request.args.get('task_id')

    with lock:
        task_info = tasks.get(user_id, {}).get(task_id)

    if not task_info:
        return f"Task {task_id} not found for user {user_id}"

    status = task_info['status']
    result = task_info['result']

    if status == 'completed':
        try:
            
            flashcards_i = json.loads(result)['terms']
            flashcards = "["
            print(flashcards_i)
            for i in flashcards_i:
                add =  str('{front: "i["term"]", back: "i["answer"]"},').replace('i["term"]', i['term']).replace('i["answer"]', i['answer'])
                flashcards += add
            flashcards = flashcards[:-1]
            flashcards += "]"
            print(flashcards)
            return render_template('result.html', placeholder=flashcards)
        except Exception as e:
            return f"Error processing result: {str(e)}"
    else:
        return f"Task is still {status}. Please check back later."

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
