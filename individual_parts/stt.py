import sounddevice as sd
import soundfile as sf
import numpy as np
import speech_recognition as sr
import time

from openai import OpenAI
from playsound import playsound
from io import BytesIO

import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.get_env("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def play_audio(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )

    response.stream_to_file("audio/output.mp3")
    playsound("audio/output.mp3")

def get_prompt():
    audio_file = open("audio/input.mp3", "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    return transcript

def get_input_file(threshold=0.03, silence_duration=3):
    recognizer = sr.Recognizer()
    with sr.Microphone() as mic:
        print("Listening for speech...")
        recognizer.adjust_for_ambient_noise(mic)
        started = False
        audio_frames = []
        silence_start_time = None

        recording = True

        def callback(indata, frames, time_info, status):
            nonlocal started, audio_frames, recording, silence_start_time
            if np.any(indata > threshold):
                if not started:
                    print("Starting recording...")
                    started = True
                audio_frames.append(indata.copy())
                silence_start_time = None  # Reset silence start time
                print("Detected sound, recording...")
            elif started:
                if silence_start_time is None:
                    silence_start_time = time.time()
                    print(f"Started silence detection at: {silence_start_time}")
                elif time.time() - silence_start_time > silence_duration:
                    print("Silence detected, stopping recording...")
                    recording = False
                    raise sd.CallbackAbort

        with sd.InputStream(callback=callback, channels=1, samplerate=16000):
            while recording:
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
            print("Audio saved as input.mp3")
        else:
            print("No speech detected")

def main():
    while True:
        get_input_file()
        user_prompt = get_prompt()
        print("Transcription:", user_prompt)
        # play_audio(user_prompt)

if __name__ == "__main__":
    main()
