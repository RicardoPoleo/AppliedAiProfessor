import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

DO_NOT_GENERATE_AUDIO = True
DO_NOT_GENERATE_RESPONSE = True

def load_script_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def split_text(text, chunk_size=20):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def generate_audio(chunk, chunk_index):
    if DO_NOT_GENERATE_AUDIO:
        return os.path.join(os.getcwd(), "audio", "output.mp3")

    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=chunk
    )
    speech_file_path = rf"C:\audio\speech_chunk_{chunk_index}.mp3"
    response.stream_to_file(speech_file_path)
    return speech_file_path

def simulate_class_session(script_file_path):
    print(f"Attempting to open file at: {script_file_path}")
    script = load_script_from_file(script_file_path)
    chunks = split_text(script, chunk_size=15)
    print(f"Generated {len(chunks)} chunks.")

    chunk_index = 1
    while chunk_index <= len(chunks):
        # Generate and play audio for the current chunk
        print(f"[Play] Chunk #{chunk_index}. Text: '{chunks[chunk_index - 1]}'")
        speech_file_path = generate_audio(chunks[chunk_index - 1], chunk_index)
        # play_audio(speech_file_path)  # Implement this function to play the audio in real-time
        
        # Check if it's time to pause for questions
        if chunk_index % 5 == 0:  # After every 5 chunks (100 words)
            pause_for_questions()
        
        chunk_index += 1

def pause_for_questions():
    print("Pausing for questions...")

    # TODO: Need to implement a way to wait for X amount of time and then read all questions.
    questions = get_questions_from_users()  
    for question in questions:
        print(f"Question received: {question}")
        answer = generate_response(question)
        response_audio_path = generate_audio(answer, "response")
        play_audio(response_audio_path)  # Play the response audio
    
    print("Resuming class...")

def generate_response(question):
    if DO_NOT_GENERATE_RESPONSE:
        return "This is a preloaded response"

    response = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
            {"role": "system", "content": "You are the AI Applied Professor, answer the following question considering we are in a Math 201 class."},
            {"role": "user", "content": f"{question}"}
          ],
          max_tokens=100
    )

    return response.choices[0].message.content

def play_audio(file_path):
    print(f"[PlayAudio] {file_path}")
    pass

def get_questions_from_users():
    # Implement a mechanism to receive text-based questions from users
    return ["Can you explain quadratic functions again?"]

# Example usage:
small_script_path = os.path.join(os.getcwd(),  "texts", "small_script.txt")
print(f"Script to read located at '{small_script_path}")
simulate_class_session(small_script_path)
