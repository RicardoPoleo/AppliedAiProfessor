import random

from flask import Flask, render_template, send_file
from flask_socketio import SocketIO, emit
import os
from OpenAIWrapper import OpenAIWrapper
from AppliedAIProfessor import AppliedAIProfessor

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Initialize OpenAI Wrapper and Applied AI Professor
openai_wrapper = OpenAIWrapper()
script_path = os.path.join(os.getcwd(), "texts", "small_script.txt")
professor = AppliedAIProfessor(openai_wrapper, script_path, socketio, do_not_generate_audio=False,
                               do_not_generate_response=False)

# Store questions in a list
questions = []


@app.route('/')
def index():
    """
    Serve the student's main page.
    """
    return render_template('student.html')


@app.route('/admin')
def admin():
    """
    Serve the admin page.
    """
    return render_template('admin.html')


@app.route('/audio/<filename>')
def stream_audio(filename):
    """
    Endpoint to stream audio to clients.

    Args:
        filename (str): The name of the audio file to stream.

    Returns:
        Response: The audio file if found, otherwise a 404 error.
    """
    file_path = os.path.join('audio', filename)
    try:
        return send_file(file_path, mimetype='audio/mp3')
    except FileNotFoundError:
        return f"Audio file '{filename}' not found at {file_path}", 404


@app.route('/upload_supporting_files')
def upload_supporting_files():
    """
    Endpoint to upload supporting files.

    Returns:
        str: Success message.
    """
    print("[Backend][upload_supporting_files] Uploading supporting files...")
    professor.trigger_support_content_upload()
    return "Supporting files uploaded successfully!", 200


@app.route('/generate_answer_from_rag_query')
def generate_answer_from_rag_query():
    """
    Endpoint to generate an answer for a question using RAG.

    Returns:
        str: The generated response.
    """
    print("[Backend][generate_answer_from_rag_query] Generating answer from RAG query...")
    student_question = "What is the definition of a derivative?"
    current_lecture = "Lecture 1"
    response = professor.generate_answer_from_rag_query(student_question, current_lecture)
    print(f"[Backend][generate_answer_from_rag_query] Response: {response}")
    return response, 200


@socketio.on('start_class')
def handle_start_class():
    """
    WebSocket event to start the class session.
    """
    print("[Backend][handle_start_class] Starting the class session.")
    professor.simulate_class_session()


@socketio.on('audio_chunk_done')
def handle_audio_chunk_done():
    """
    WebSocket event to send the next audio chunk.
    """
    next_chunk = professor.get_next_chunk()
    if next_chunk:
        socketio.emit('next_audio_chunk', {'audioFile': next_chunk})
    else:
        print("[Backend][handle_audio_chunk_done] There is no more audio to play.")


@socketio.on('stream_message')
def handle_stream_message(data):
    """
    WebSocket event to generate audio for a message.

    Args:
        data (dict): Contains the message to generate audio for.
    """
    print(f"[Backend][handle_stream_message] Generating audio for message: {data['message']}")
    name_of_file = generate_random_audio_name()
    path_to_audio = professor.generate_audio_from_text(data['message'], name_of_file)
    print(f"[Backend][handle_stream_message] Audio generated at: {path_to_audio}")
    socketio.emit('next_audio_chunk', {'audioFile': name_of_file})


def generate_random_audio_name():
    """
    Generate a random name for an audio file.

    Returns:
        str: The generated audio file name.
    """
    random_number = random.randint(0, 1000)
    name_of_file = f'stream_message_{random_number}.mp3'
    return name_of_file


@socketio.on('submit_question')
def handle_question(data):
    """
    WebSocket event to handle a submitted question.

    Args:
        data (dict): Contains the question and optionally the student's name.
    """
    question = data['question']
    student_name = data.get('name', 'Anonymous')
    print(f"[Backend] Received question from {student_name}: {question}")
    questions.append({'question': question, 'name': student_name, 'answered': False})
    emit('receive_response', {'response': "Your question has been received.", 'question': question}, broadcast=True)


@socketio.on('pause_class')
def handle_pause_class():
    """
    WebSocket event to pause the class session.
    """
    print("[Backend][handle_pause_class] Pausing the class session.")
    professor.handle_pending_questions(questions)


@socketio.on('submit_admin_question')
def handle_generate_response_for_admin(data):
    """
    WebSocket event to generate a response for an admin question.

    Args:
        data (dict): Contains the question and optionally the voice model.
    """
    print(f'[Backend][handle_generate_response] Generating response for question {data["question"]}')
    response = professor.generate_text_response_for_question(data)
    emit('receive_response', {'response': response, 'question': data["question"]}, broadcast=True)

    name_of_file = generate_random_audio_name()
    print(f'[Backend][handle_generate_response] Generating audio "{name_of_file}" for response: {response}')
    response_audio_path = professor.openai_wrapper.generate_audio(response, name_of_file,
                                                                  professor.do_not_generate_audio,
                                                                  voice_model=data.get('voice_model', 'alloy'))
    print(f'[Backend][handle_generate_response] Audio generated at: {response_audio_path}')
    socketio.emit('next_audio_chunk', {'audioFile': name_of_file})


@socketio.on('resume_class')
def handle_resume_class():
    """
    WebSocket event to resume the class session.
    """
    print("[Backend][handle_resume_class] Resuming the class session.")
    next_chunk = professor.get_next_chunk()
    if next_chunk:
        socketio.emit('next_audio_chunk', {'audioFile': next_chunk})
    else:
        print("[Backend][handle_resume_class] There is no more audio to play.")


@socketio.on('end_class')
def handle_end_class():
    """
    WebSocket event to end the class session.
    """
    print("[Backend][handle_end_class] Ending the class session.")
    socketio.emit('class_ended', broadcast=True)


if __name__ == '__main__':
    """
    Main entry point for the backend server.
    """
    print(f"Python version: {os.system('python --version')}")

    if not os.path.exists('audio'):
        os.makedirs('audio')

    if not os.path.exists('templates'):
        os.makedirs('templates')

    if not os.path.exists('texts'):
        os.makedirs('texts')

    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)
