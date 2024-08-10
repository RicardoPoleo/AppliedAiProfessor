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
professor = AppliedAIProfessor(openai_wrapper, script_path, socketio, do_not_generate_audio=True, do_not_generate_response=True)

# Serve the student's main page
@app.route('/')
def index():
    return render_template('index.html')

# Serve the admin page
@app.route('/admin')
def admin():
    return render_template('admin.html')

# Endpoint to stream audio to clients
@app.route('/audio/<filename>')
def stream_audio(filename):
    try:
        return send_file(f'./audio/{filename}', mimetype='audio/mp3')
    except FileNotFoundError:
        return "Audio file not found", 404

# WebSocket event to start the class
@socketio.on('start_class')
def handle_start_class():
    print("Class started by admin")
    professor.simulate_class_session()

# WebSocket event to send the next audio chunk
@socketio.on('audio_chunk_done')
def handle_audio_chunk_done():
    next_chunk = professor.get_next_chunk()
    if next_chunk:
        socketio.emit('next_audio_chunk', {'audioFile': next_chunk})
    else:
        print("Class has ended.")

# WebSocket event to handle question submission
@socketio.on('submit_question')
def handle_question(data):
    question = data['question']
    print(f"Received question: {question}")
    response = professor.openai_wrapper.generate_response(question, professor.do_not_generate_response)
    response_audio_path = professor.openai_wrapper.generate_audio(response, "response.mp3", professor.do_not_generate_audio)
    emit('receive_response', {'response': response}, broadcast=True)
    professor.stream_audio_to_students(response_audio_path)

if __name__ == '__main__':
    socketio.run(app, debug=True)
