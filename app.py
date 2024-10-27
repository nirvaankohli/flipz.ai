from flask import Flask, render_template, redirect, url_for, session, request, jsonify, send_from_directory
import CardinalisAPI
import time
import json
from threading import Thread
import os
from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

#loading key


app = Flask(__name__)

app.secret_key = key

api = CardinalisAPI.API(key)
global result
from flask import url_for

def generate_flashcards(topic, grade_level):

    global task_status 
    task_status= False
    #session['task_status'] = False


    flashcards = api.flashcards(topic, grade_level)
    
    #session['task_status'] = True
    task_status = True
    global result

    result = flashcards

    #return flashcards, task_status

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        topic = request.form['topic']
        grade_level = request.form['grade']

        session['generation'] = {'topic': topic, 'grade': grade_level}
        
        return redirect(url_for('loading'))
        
    else:
        return render_template('index.html')


@app.route('/loading', methods=['GET', 'POST'])

def loading():

    thread = Thread(target=generate_flashcards, args=(session['generation']['topic'], session['generation']['grade']))
    thread.start()


    print("i am redirecting to the cool loading")
    return redirect(url_for('loading_cards'))
    
@app.route('/loading_cards', methods=['GET', 'POST'])

def loading_cards():

    print("i am in the cool loading")

    return render_template('generation.html')
    
@app.route('/check_status', methods=['GET', 'POST'])

def check_status():
    return str(task_status)

@app.route('/flashcards', methods=['GET', 'POST'])
def flashcards():

    topic = session['generation']['topic']
    grade_level = session['generation']['grade']

    data = json.loads((result['choices'][0]['message']['content']))
    print(type(data))
    print(data)
    questions = data["questions"]
    answers = data["answers"]
    
    accordians = []

    

    if len(questions) == len(answers):
        for i in range(len(questions)):

            accordians.append({"front": questions[i], "back": answers[i]})
           

    return render_template('flashcardinfo.html', flashcard_cool_info = accordians)


if __name__ == '__main__':
    app.run(debug=True)

