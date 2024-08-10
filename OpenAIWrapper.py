import os
from dotenv import load_dotenv
from openai import OpenAI

class OpenAIWrapper:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

    def generate_audio(self, text, filename, do_not_generate=False):
        if do_not_generate:
            # the_file_path = os.path.join(os.getcwd(), 'audio', 'speech_chunk_1.mp3')
            the_file_path = 'speech_chunk_1.mp3'
            print(f"[OpenAIWrapper.generate_audio] Generated audio path: {the_file_path}")
            return the_file_path

        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        speech_file_path = os.path.join(os.getcwd(), "audio", filename)
        response.stream_to_file(speech_file_path)
        return speech_file_path

    def generate_response(self, question, do_not_generate=False):
        if do_not_generate:
            return "This is a preloaded response"

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are the AI Applied Professor, answer the following question considering we are in a Math 201 class."},
                {"role": "user", "content": question}
            ],
            max_tokens=100
        )

        return response.choices[0].message.content
