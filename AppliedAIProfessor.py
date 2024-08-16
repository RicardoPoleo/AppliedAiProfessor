import os
import random


def generate_random_audio_name():
    """
    Generate a random name for an audio file.

    Returns:
        str: The generated audio file name.
    """
    random_number = random.randint(0, 1000)
    name_of_file = f'stream_message_{random_number}.mp3'
    return name_of_file


class AppliedAIProfessor:
    def __init__(self, openai_wrapper, script_path, socketio, do_not_generate_audio=False,
                 do_not_generate_response=False):
        """
        Initialize the AppliedAIProfessor class.

        Args:
            openai_wrapper (OpenAIWrapper): Instance of OpenAIWrapper for API interactions.
            script_path (str): Path to the lecture script file.
            socketio (SocketIO): Instance of SocketIO for real-time communication.
            do_not_generate_audio (bool): Flag to disable audio generation.
            do_not_generate_response (bool): Flag to disable response generation.
        """
        self.openai_wrapper = openai_wrapper
        self.script_path = script_path
        self.socketio = socketio  # Store the socketio instance
        self.do_not_generate_audio = do_not_generate_audio
        self.do_not_generate_response = do_not_generate_response
        self.chunks = []
        self.chunk_size = 20
        self.current_chunk_index = 0  # Track the current chunk index
        self.questions = []  # Store questions from users

    def load_script_from_file(self):
        """
        Load the lecture script from a file.

        Returns:
            str: The content of the script file.
        """
        with open(self.script_path, 'r') as file:
            return file.read()

    def split_text(self, text):
        """
        Split the text into chunks of a specified size.

        Args:
            text (str): The text to be split.
        """
        words = text.split()
        self.chunks = [' '.join(words[i:i + self.chunk_size]) for i in range(0, len(words), self.chunk_size)]

    def simulate_class_session(self):
        """
        Simulate a class session by splitting the script into chunks and emitting the first chunk.
        """
        print(f"[AppliedAiProfessor.simulate_class_session] Attempting to open file at: {self.script_path}")
        script = self.load_script_from_file()
        self.split_text(script)
        print(f"[AppliedAiProfessor.simulate_class_session] Generated {len(self.chunks)} chunks.")

        first_chunk = self.get_next_chunk()
        print(f"[AppliedAiProfessor.simulate_class_session] {first_chunk}")
        self.socketio.emit('start_class', {'audioFile': first_chunk})

    def get_next_chunk(self):
        """
        Get the next chunk of the script and generate audio for it.

        Returns:
            str: The name of the audio file for the next chunk, or None if no more chunks are available.
        """
        print(f"[AppliedAiProfessor.get_next_chunk] Current chunk index: {len(self.chunks)}/{self.current_chunk_index}")
        if self.current_chunk_index < len(self.chunks):
            chunk_text = self.chunks[self.current_chunk_index]
            print(f"[AppliedAiProfessor.get_next_chunk] Chunk #{self.current_chunk_index + 1}. Text: '{chunk_text}'")
            audio_file = self.openai_wrapper.generate_audio(chunk_text,
                                                            f"speech_chunk_{self.current_chunk_index + 1}.mp3",
                                                            self.do_not_generate_audio)
            self.current_chunk_index += 1
            return os.path.basename(audio_file)
        else:
            return None

    def handle_pending_questions(self, questions):
        """
        Handle pending questions by generating and streaming audio responses.

        Args:
            questions (list): List of questions to be answered.
        """
        print(f"[AppliedAiProfessor.pause_for_questions] Pausing for questions. Received {len(questions)} questions")
        print(f"[AppliedAiProfessor.pause_for_questions] Questions: {questions}")
        unanswered_questions = [q for q in questions if not q['answered']]
        for question in unanswered_questions:
            # This works but is not rag related
            # answer = self.generate_text_response_for_question(question)

            # This is the RAG related code
            answer = self.generate_answer_from_rag_query(question, self.get_current_lecture_name())

            response_filename = generate_random_audio_name()

            response_audio_path = self.openai_wrapper.generate_audio(answer, response_filename, False)
            print(f"[AppliedAiProfessor.pause_for_questions] Generated audio response: {response_audio_path}")
            question['answered'] = True
            self.stream_audio_to_students(response_filename)

        print("[AppliedAiProfessor.pause_for_questions] Resuming class...")

    def generate_text_response_for_question(self, question):
        """
        Generate a text response for a given question.

        Args:
            question (dict): The question to generate a response for.

        Returns:
            str: The generated text response.
        """
        print(f"[AppliedAiProfessor.generate_text_response_for_question] "
              f"Student '{question['name']}' asked '{question['question']}'")
        answer = self.openai_wrapper.generate_response(question, self.do_not_generate_response)
        return answer

    def stream_audio_to_students(self, file_path):
        """
        Stream an audio file to students.

        Args:
            file_path (str): The path to the audio file to be streamed.
        """
        print(f"[AppliedAiProfessor.stream_audio_to_students] {file_path}")
        self.socketio.emit('next_audio_chunk', {'audioFile': file_path})  # Emit the next audio chunk

    def generate_audio_from_text(self, text, filename):
        """
        Generate an audio file from the given text.

        Args:
            text (str): The text to generate audio for.
            filename (str): The name of the audio file to be generated.

        Returns:
            str: The path to the generated audio file.
        """
        print(f"[AppliedAiProfessor.generate_audio_from_text] Generating audio for text: {text}")
        return self.openai_wrapper.generate_audio(text, filename, self.do_not_generate_audio)

    def trigger_support_content_upload(self):
        """
        Trigger the upload of support content by setting up the RAG assistant.
        """
        print(f"[AppliedAiProfessor.trigger_support_content_upload] Triggering support content upload")
        assistant, vector_store = self.openai_wrapper.setup_rag_assistant()
        print(
            f"[AppliedAiProfessor.trigger_support_content_upload] Assistant: {assistant.id}, Vector Store: {vector_store.id}")

    def generate_answer_from_rag_query(self, question, current_lecture):
        """
        Generate an answer for a question using a RAG query.

        Args:
            question (str): The question to generate an answer for.
            current_lecture (str): The current lecture context.

        Returns:
            str: The generated answer.
        """
        print(f"[AppliedAiProfessor.run_rag_query] Running RAG query for question: '{question}'")
        rag_response = self.openai_wrapper.run_rag_query(question, current_lecture)
        print(f"[AppliedAiProfessor.run_rag_query] Response: {rag_response}")
        return rag_response

    def get_current_lecture_name(self):
        """
        Get the name of the current lecture.

        Returns:
            str: The name of the current lecture.
        """
        return "Lecture 1"
