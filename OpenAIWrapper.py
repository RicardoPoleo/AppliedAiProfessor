import os
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI


class OpenAIWrapper:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

    def generate_audio(self, text: str, filename: str, do_not_generate: bool = False, voice_model: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "alloy") -> str:
        if do_not_generate:
            the_file_path = 'speech_chunk_1.mp3'
            print(f"[OpenAIWrapper.generate_audio] Dummy response returned from path '{the_file_path}'")
            return the_file_path

        print(f"[OpenAIWrapper.generate_audio] Generating audio with voice model '{voice_model}' for text: {text}")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice_model,
            input=text
        )

        speech_file_path = os.path.join(os.getcwd(), "audio", filename)
        print(f"[OpenAIWrapper.generate_audio] Saving audio to path: {speech_file_path}")
        response.stream_to_file(speech_file_path)
        return speech_file_path

    def generate_response(self, question, do_not_generate=False):
        if do_not_generate:
            return "This is a preloaded response"

        print(f"[OpenAIWrapper.generate_response] Generating response for question: {question['question']}")

        personality = f"""
        friendly and professional
        """

        class_name = "Math 201 class"

        limitations = f"""
        The response should not contain emojis or slang. Shouldn't be longer than one or two sentences.
        """

        instruction = f"""
        You are the AI Applied Professor, answer the following question considering we are in a {class_name}. 
        Your response should contain the question made by the student and the answer to the question. 
        The response should be in a {personality} manner. 
        {limitations}.
        The student is asking a question is named '{question["name"]}'.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": question["question"]}
            ],
            max_tokens=100
        )

        return response.choices[0].message.content
