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
                               do_not_generate_response=True)


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
    file_path = os.path.join('audio', filename)
    try:
        return send_file(file_path, mimetype='audio/mp3')
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
    student_name = data.get('name', 'Anonymous')
    print(f"[Backend] Received question from {student_name}: {question}")
    response = professor.openai_wrapper.generate_response(question, professor.do_not_generate_response)
    response_audio_path = professor.openai_wrapper.generate_audio(response, "response.mp3",
                                                                  professor.do_not_generate_audio)
    emit('receive_response', {'response': response, 'question': question}, broadcast=True)
    professor.stream_audio_to_students(response_audio_path)


# WebSocket event to pause the class
@socketio.on('pause_class')
def handle_pause_class():
    print("Class paused by admin")
    professor.pause_for_questions()


# WebSocket event to resume the class
@socketio.on('resume_class')
def handle_resume_class():
    print("Class resumed by admin")
    next_chunk = professor.get_next_chunk()
    if next_chunk:
        socketio.emit('next_audio_chunk', {'audioFile': next_chunk})
    else:
        print("Class has ended.")


# WebSocket event to end the class
@socketio.on('end_class')
def handle_end_class():
    print("Class ended by admin")
    socketio.emit('class_ended', broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
