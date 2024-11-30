from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response
import threading
import uuid
import CardinalisAPI
import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = key
user_id = None
api = CardinalisAPI.API(key)

form_data = {}
outcome = 'None'
result = 'None'
tasks = {}
task_status = "Not Started"

def api_call(topic, level, user_id, task_id):
    global task_status
    global outcome
    try:
        tasks[user_id + str(task_id)] = ['in progress', 'None']


        result = api.flashcards(topic, level)
        outcome = result
        print('success')

        tasks[user_id + str(task_id)] = ['completed', result]

        return 
        
        
    except Exception as e:

        task_status = f"Failed for task {task_id}: {str(e)}"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/', methods=['GET', 'POST'])
def home():
    global user_id
    if request.method == 'POST':
        import secrets
        form_data = {}
        form_data['topic'] = request.form['topic']
        form_data['level'] = request.form['level']
        form_data['user_id'] = request.cookies.get('user_id')
        form_data['task_id'] = secrets.token_hex(5)
        
        # Start the API call in a background thread with arguments
        background_thread = threading.Thread(target=api_call, args=(form_data['topic'], form_data['level'], form_data['user_id'], form_data['task_id']))
        background_thread.start()
        
        return redirect(url_for('loading_cards', task_id=form_data['task_id']))
        
    else:
        user_id = request.cookies.get('user_id')
        if not user_id:
            user_id = str(uuid.uuid4())
        
        response = make_response(render_template('home.html'))
        response.set_cookie('user_id', user_id, max_age=60*60*24*30*12)  
        return response


@app.route('/loading_cards', methods=['GET', 'POST'])
def loading_cards():
    global user_id
    if user_id is None:
        user_id = request.cookies.get('user_id')
        if not user_id:
            user_id = str(uuid.uuid4())

    task_id = request.args.get('task_id')
    return render_template('generation.html', task_id=task_id)


@app.route('/check_status', methods=['GET'])
def check_status():
    user_id = request.cookies.get('user_id')
    task_id = request.args.get('task_id')
    if user_id and task_id and (user_id + str(task_id)) in tasks:

        status, result = tasks[user_id + str(task_id)]
        return jsonify({"status": status, "result": result})
    
    return jsonify({"status": "unknown"})

@app.route('/show_result', methods=['GET'])
def show_result():

    user_id = request.cookies.get('user_id')
    task_id = request.args.get('task_id')

    if user_id+task_id in tasks.keys():

        status = tasks[user_id + str(task_id)][0]

        flashcards_i = json.loads(outcome)['terms']
        flashcards = "["
        for i in flashcards_i:
            add =  str('{front: "i["term"]", back: "i["answer"]"},').replace('i["term"]', i['term']).replace('i["answer"]', i['answer'])
            flashcards += add
        flashcards = flashcards[:-1]
        flashcards += "]"



        return render_template('result.html', placeholder = flashcards)
    return "The thing is not in tasks/not ready"

if __name__ == '__main__':

    app.run(debug=True, threaded=True) 


