import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def load_script_from_file(file_path):
    print(f"Loading the script from '{file_path}'.")
    with open(file_path, 'r') as file:
        return file.read()

def split_text(text, chunk_size=20):
    print(f"Generating chunks of text every {chunk_size} words.")
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

script_file_path = rf"C:\projects\sports-buddy\initial_scripts.txt"
script = load_script_from_file(script_file_path)

chunks = split_text(script, chunk_size=20)

pause_text = "Question to class: Do we have any question so far?"
extended_chunks = []
for i, chunk in enumerate(chunks):
    extended_chunks.append(chunk)
    if (i + 1) % 5 == 0: 
        extended_chunks.append(pause_text)

for i, chunk in enumerate(extended_chunks):
    print(f"Generating audio for chunk {i + 1}/{len(extended_chunks)}")
    print(chunk)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=chunk
    )
    speech_file_path = rf"C:\audio\speech_chunk_{i + 1}.mp3"
    response.stream_to_file(speech_file_path)
    print(f"Saved: {speech_file_path}")
