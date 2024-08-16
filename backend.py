import random

from flask import Flask, render_template, send_file
from flask_socketio import SocketIO, emit
import os
from OpenAIWrapper import OpenAIWrapper
from AppliedAIProfessor import AppliedAIProfessor

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize OpenAI Wrapper and Applied AI Professor
openai_wrapper = OpenAIWrapper()
script_path = os.path.join(os.getcwd(), "texts", "small_script.txt")
professor = AppliedAIProfessor(openai_wrapper, script_path, socketio, do_not_generate_audio=False,
                               do_not_generate_response=False)

# Store questions in a list
questions = []


# Serve the student's main page
@app.route('/')
def index():
    return render_template('student.html')


# Serve the admin page
@app.route('/admin')
def admin():
    return render_template('admin.html')


# Endpoint to stream audio to clients
@app.route('/audio/<filename>')
def stream_audio(filename):
    file_path = os.path.join('audio', filename)
    try:
        return send_file(file_path, mimetype='audio/mp3')
    except FileNotFoundError:
        return "Audio file not found", 404


# WebSocket event to start the class
@socketio.on('start_class')
def handle_start_class():
    print("[Backend][handle_start_class] Starting the class session.")
    professor.simulate_class_session()


# WebSocket event to send the next audio chunk
@socketio.on('audio_chunk_done')
def handle_audio_chunk_done():
    next_chunk = professor.get_next_chunk()
    if next_chunk:
        socketio.emit('next_audio_chunk', {'audioFile': next_chunk})
    else:
        print("[Backend][handle_audio_chunk_done] There is no more audio to play.")


@socketio.on('stream_message')
def handle_stream_message(data):
    print(f"[Backend][handle_stream_message] Generating audio for message: {data['message']}")
    # Generate a random number from 0 to 1000
    name_of_file = generate_random_audio_name()
    path_to_audio = professor.generate_audio_from_text(data['message'], name_of_file)
    print(f"[Backend][handle_stream_message] Audio generated at: {path_to_audio}")
    socketio.emit('next_audio_chunk', {'audioFile': name_of_file})


def generate_random_audio_name():
    random_number = random.randint(0, 1000)
    name_of_file = f'stream_message_{random_number}.mp3'
    return name_of_file


# WebSocket event to handle question submission
@socketio.on('submit_question')
def handle_question(data):
    question = data['question']
    student_name = data.get('name', 'Anonymous')
    print(f"[Backend] Received question from {student_name}: {question}")
    questions.append({'question': question, 'name': student_name, 'answered': False})
    emit('receive_response', {'response': "Your question has been received.", 'question': question}, broadcast=True)


# WebSocket event to pause the class
@socketio.on('pause_class')
def handle_pause_class():
    print("[Backend][handle_pause_class] Pausing the class session.")
    professor.handle_pending_questions(questions)


# This method takes the question and generates a response
@socketio.on('submit_admin_question')
def handle_generate_response_for_admin(data):
    print(f'[Backend][handle_generate_response] Generating response for question {data["question"]}')
    response = professor.generate_text_response_for_question(data)
    emit('receive_response', {'response': response, 'question': data["question"]}, broadcast=True)

    # Emit the response audio
    name_of_file = generate_random_audio_name()
    print(f'[Backend][handle_generate_response] Generating audio "{name_of_file}" for response: {response}')
    response_audio_path = professor.openai_wrapper.generate_audio(response, name_of_file,
                                                                  professor.do_not_generate_audio,
                                                                  voice_model=data.get('voice_model', 'alloy'))
    print(f'[Backend][handle_generate_response] Audio generated at: {response_audio_path}')
    socketio.emit('next_audio_chunk', {'audioFile': name_of_file})


# WebSocket event to resume the class
@socketio.on('resume_class')
def handle_resume_class():
    print("[Backend][handle_resume_class] Resuming the class session.")
    next_chunk = professor.get_next_chunk()
    if next_chunk:
        socketio.emit('next_audio_chunk', {'audioFile': next_chunk})
    else:
        print("[Backend][handle_resume_class] There is no more audio to play.")


# WebSocket event to end the class
@socketio.on('end_class')
def handle_end_class():
    print("[Backend][handle_end_class] Ending the class session.")
    socketio.emit('class_ended', broadcast=True)


if __name__ == '__main__':
    # Print Python version
    print(f"Python version: {os.system('python --version')}")

    if not os.path.exists('audio'):
        os.makedirs('audio')

    if not os.path.exists('templates'):
        os.makedirs('templates')

    if not os.path.exists('texts'):
        os.makedirs('texts')

    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)
