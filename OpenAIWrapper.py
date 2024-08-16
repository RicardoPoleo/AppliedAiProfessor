import os
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler


class OpenAIWrapper:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.vector_store = None
        self.assistant = None

    def generate_audio(self, text: str, filename: str, do_not_generate: bool = False,
                       voice_model: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "alloy") -> str:
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

    def setup_rag_assistant(self, assistant_name: str, vector_store_name: str, instruction_text: str, file_paths: list):
        print(
            f"[OpenAIWrapper.setup_rag_assistant] Setting up RAG assistant '{assistant_name}' with vector store '{vector_store_name}'")

        self.assistant = self.client.beta.assistants.create(
            name=assistant_name,
            instructions=instruction_text,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )

        self.vector_store = self.client.beta.vector_stores.create(name=vector_store_name)

        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=self.vector_store.id, files=file_streams
        )

        print(f"[OpenAIWrapper.setup_rag_assistant] File batch status: {file_batch.status}")
        print(f"[OpenAIWrapper.setup_rag_assistant] File counts: {file_batch.file_counts}")

    def run_rag_query(self, student_question: str, current_lecture: str, handler=None):
        print(f"[OpenAIWrapper.run_rag_query] Running RAG query for question: '{student_question}'")

        if not self.assistant or not self.vector_store:
            raise ValueError("RAG assistant or vector store not set up. Please call setup_rag_assistant first.")

        thread = self.client.beta.threads.create(
            messages=[{"role": "user", "content": student_question}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [self.vector_store.id]
                }
            }
        )

        instruction_for_search = "Search in which lecture the requested concept is explained. If it appears in another Lecture that is not the current lecture, reply explaining that the concept is out of the scope of this class (in a friendly manner), since it will be explained in the lecture X, where X is the lecture where it appears."
        length_limitation = "Keep your answers short, no longer than 2 sentences."
        tone_instructions = "Answer in a friendly and formal manner."

        instruction_text = f"We are currently on {current_lecture}. {instruction_for_search}. {length_limitation}. {tone_instructions}"

        event_handler = handler if handler else EventHandler()

        with self.client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=self.assistant.id,
                instructions=instruction_text,
                event_handler=event_handler,
        ) as stream:
            stream.until_done()


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(message_content.value)
        print("\n".join(citations))


# Example Usage:
# wrapper = OpenAIWrapper()
#
# # Initialize and upload files for the RAG assistant
# wrapper.setup_rag_assistant(
#     assistant_name="Math professor",
#     vector_store_name="Math 201 lecture",
#     instruction_text="You are a Math professor. Use your knowledge base to answer questions about math lectures based on the provided files.",
#     file_paths=["C:\\projects\\Sports-Buddy\\support_material\\Lecture01_Script.pdf",
#                 "C:\\projects\\Sports-Buddy\\support_material\\Lecture02_Script.pdf"]
# )
#
# # Run a RAG-based query
# wrapper.run_rag_query(student_question="Can you explain what functions are?", current_lecture="Lecture 1")
