from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, make_response, session
import threading
import uuid
import CardinalisAPI
import json
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = key
api = CardinalisAPI.API(key)

def api_call(topic, level, user_id, task_id):
    """Background API call to generate flashcards."""
    try:
        # Store task as 'in progress' in the session
        task_key = f"task_{task_id}"
        session[task_key] = {'status': 'in progress', 'result': None}
        
        # Simulate API call
        result = api.flashcards(topic, level)
        session[task_key] = {'status': 'completed', 'result': result}

    except Exception as e:
        # Update task status to failed
        task_key = f"task_{task_id}"
        session[task_key] = {'status': 'failed', 'result': str(e)}

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/', methods=['GET', 'POST'])
def home():
    """Render the home page or start a new task."""
    if request.method == 'POST':
        form_data = {
            'topic': request.form['topic'],
            'level': request.form['level'],
            'task_id': uuid.uuid4().hex
        }

        # Store user ID in session
        session['user_id'] = request.cookies.get('user_id', str(uuid.uuid4()))
        session['current_task'] = form_data['task_id']

        # Start the API call in a background thread
        threading.Thread(target=api_call, args=(form_data['topic'], form_data['level'], session['user_id'], form_data['task_id'])).start()
        return redirect(url_for('loading_cards'))
    else:
        user_id = request.cookies.get('user_id', str(uuid.uuid4()))
        response = make_response(render_template('home.html'))
        response.set_cookie('user_id', user_id, max_age=60*60*24*30*12)  # 1 year
        return response

@app.route('/loading_cards', methods=['GET'])
def loading_cards():
    """Render the loading page."""
    return render_template('generation.html', task_id=session.get('current_task'))

@app.route('/check_status', methods=['GET'])
def check_status():
    """Check the status of a task."""
    task_id = session.get('current_task')
    task_key = f"task_{task_id}"
    task_data = session.get(task_key, {'status': 'unknown', 'result': None})
    return jsonify(task_data)

@app.route('/show_result', methods=['GET'])
def show_result():
    """Show the result of a completed task."""
    task_id = session.get('current_task')
    task_key = f"task_{task_id}"
    task_data = session.get(task_key)

    if task_data and task_data['status'] == 'completed':
        try:
            flashcards = json.loads(task_data['result'])['terms']
            formatted_flashcards = json.dumps([
                {"front": card["term"], "back": card["answer"]} for card in flashcards
            ])
            return render_template('result.html', placeholder=formatted_flashcards)
        except Exception:
            pass
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
