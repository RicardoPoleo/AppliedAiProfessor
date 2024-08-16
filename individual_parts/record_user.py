import streamlit as st
import sounddevice as sd
import soundfile as sf
import numpy as np
import speech_recognition as sr
import os

from openai import OpenAI
from playsound import playsound
from io import BytesIO

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.get_env("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Function to play audio from text
def play_audio(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    if not os.path.exists('audio'):
        os.makedirs('audio')
    response.stream_to_file("audio/output.mp3")
    playsound("audio/output.mp3")

# Function to get transcription from audio file
def get_prompt():
    with open("audio/input.mp3", "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return transcript

# Function to handle recording
def record_audio(threshold=0.03):
    recognizer = sr.Recognizer()
    with sr.Microphone() as mic:
        st.write("Listening for speech...")
        recognizer.adjust_for_ambient_noise(mic)
        audio_frames = []

        def callback(indata, frames, time_info, status):
            if np.any(indata > threshold):
                audio_frames.append(indata.copy())
                st.write("Detected sound, recording...")

        with sd.InputStream(callback=callback, channels=1, samplerate=16000):
            while st.session_state.recording:
                sd.sleep(100)

        if audio_frames:
            audio_data = np.concatenate(audio_frames, axis=0)
            if not os.path.exists('audio'):
                os.makedirs('audio')
            with BytesIO() as f:
                sf.write(f, audio_data, samplerate=16000, format='WAV')
                f.seek(0)
                with sr.AudioFile(f) as source:
                    audio = recognizer.record(source)
                    with open("audio/input.mp3", "wb") as mp3_file:
                        mp3_file.write(audio.get_wav_data(convert_rate=16000, convert_width=2))
            st.write("Audio saved as input.mp3")
        else:
            st.write("No speech detected")

# Main function to run the Streamlit app
def main():
    st.title("Speech-to-Text and Text-to-Speech App")

    if "recording" not in st.session_state:
        st.session_state.recording = False

    if st.session_state.recording:
        if st.button("Stop Recording"):
            st.session_state.recording = False
            st.write("Recording stopped.")
            user_prompt = get_prompt()
            st.write("Transcription:", user_prompt)
            play_audio(user_prompt)
            st.success("Process Completed")
    else:
        if st.button("Start Recording"):
            st.session_state.recording = True
            st.write("Recording started...")
            with st.spinner('Recording...'):
                record_audio()

if __name__ == "__main__":
    main()
