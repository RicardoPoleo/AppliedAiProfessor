import os
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler


class OpenAIWrapper:
    def __init__(self):
        self.thread = None
        self.file_batch = None
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

    def setup_rag_assistant(self):
        file_paths = ["C:\\projects\\Sports-Buddy\\support_material\\Lecture01_Script.pdf",
                      "C:\\projects\\Sports-Buddy\\support_material\\Lecture02_Script.pdf"]

        instruction_text = ("You are a Math professor. Use your knowledge base to answer questions about math lectures "
                            "based on the provided files.")

        print(f"[OpenAIWrapper.setup_rag_assistant] file_paths: {file_paths}")
        assistant_name = "Math professor"
        vector_store_name = "Math 201 lecture"

        print(f"[OpenAIWrapper.setup_rag_assistant] Setting up RAG assistant with name '{assistant_name}'")
        self.assistant = self.client.beta.assistants.create(
            name=assistant_name,
            instructions=instruction_text,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )
        print(f"[OpenAIWrapper.setup_rag_assistant] Assistant ID: {self.assistant.id}")

        if not self.vector_store:
            print(f"[OpenAIWrapper.setup_rag_assistant] Creating vector store with name '{vector_store_name}'")
            self.vector_store = self.client.beta.vector_stores.create(name=vector_store_name)
        print(f"[OpenAIWrapper.setup_rag_assistant] Vector store ID: {self.vector_store.id}")

        if not self.file_batch:
            print(f"[OpenAIWrapper.setup_rag_assistant] Uploading files to vector store")
            file_streams = [open(path, "rb") for path in file_paths]
            self.file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=self.vector_store.id, files=file_streams
            )
        print(f"[OpenAIWrapper.setup_rag_assistant] File batch status: {self.file_batch.status}")
        print(f"[OpenAIWrapper.setup_rag_assistant] File counts: {self.file_batch.file_counts}")
        return self.assistant, self.vector_store

    def run_rag_query(self, question: str, current_lecture: str, handler=None):
        print(f"[OpenAIWrapper.run_rag_query] Running RAG query for question: '{question}'")

        if not self.assistant or not self.vector_store:
            raise ValueError("RAG assistant or vector store not set up. Please call setup_rag_assistant first.")

        question_text = ""
        if "question" not in question:
            question_text = question
        else:
            question_text = question["question"]

        self.thread = self.client.beta.threads.create(
            messages=[{"role": "user", "content": question_text}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [self.vector_store.id]
                }
            }
        )

        instruction_for_search = ("Search in which lecture the requested concept is explained. "
                                  "If it appears in another Lecture that is not the current lecture,"
                                  " reply explaining that the concept is out of the scope of this class "
                                  "(in a friendly manner), since it will be explained in the lecture X, where X is the "
                                  "lecture where it appears."
                                  "If the concept is not in any lecture, reply that the concept is not in the material but we can review it after the class."
                                  "If the concept is in the current lecture, reply with the explanation.")

        length_limitation = "Keep your answers short, no longer than 2 sentences."
        student_name = question["name"] if "name" in question else "No name provided"
        tone_instructions = (f"Answer in a friendly and formal manner. Always refer to the student by their name. "
                             f"This student is named {student_name}.")

        instruction_text = f"We are currently on {current_lecture}. {instruction_for_search}. {length_limitation}. {tone_instructions}"

        event_handler = handler if handler else EventHandler()
        event_handler.set_client(self.client)

        with self.client.beta.threads.runs.stream(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instruction_text,
                event_handler=event_handler,
        ) as stream:
            stream.until_done()

        print(f"[OpenAIWrapper.run_rag_query] RAG query completed. Thread ID: {self.thread.id} is done. "
              f"Response: {stream}")

        response = event_handler.get_final_response()
        print(f"[OpenAIWrapper.run_rag_query] Final response: {response}")

        return response


class EventHandler(AssistantEventHandler):
    # Method to set the client
    def __init__(self):
        super().__init__()
        self.citations = []
        self.client = None
        self.final_response = ""

    def set_client(self, client):
        self.client = client

    @override
    def on_text_created(self, text) -> None:
        print(f"\nAssistant 1 > ", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nAssistant 2 > {tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        message_content = message.content[0].text
        annotations = message_content.annotations
        self.citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = self.client.files.retrieve(file_citation.file_id)
                self.citations.append(f"[{index}] {cited_file.filename}")

        print(f"message_content.value: {message_content.value}")
        joined = ",".join(self.citations)
        print(f"Citations for this message: {joined}")
        print("\n".join(self.citations))

        self.final_response = message_content.value

    # Return the final response
    def get_final_response(self):
        return self.final_response

    # Method that returns the response

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
