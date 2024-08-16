import os


class AppliedAIProfessor:
    def __init__(self, openai_wrapper, script_path, socketio, do_not_generate_audio=True,
                 do_not_generate_response=True):
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
        with open(self.script_path, 'r') as file:
            return file.read()

    def split_text(self, text):
        words = text.split()
        self.chunks = [' '.join(words[i:i + self.chunk_size]) for i in range(0, len(words), self.chunk_size)]

    def simulate_class_session(self):
        print(f"[AppliedAiProfessor.simulate_class_session] Attempting to open file at: {self.script_path}")
        script = self.load_script_from_file()
        self.split_text(script)
        print(f"[AppliedAiProfessor.simulate_class_session] Generated {len(self.chunks)} chunks.")

        first_chunk = self.get_next_chunk()
        print(f"[AppliedAiProfessor.simulate_class_session] {first_chunk}")
        self.socketio.emit('start_class', {'audioFile': first_chunk})

    def get_next_chunk(self):
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
        print(f"[AppliedAiProfessor.pause_for_questions] Pausing for questions. Received {len(questions)} questions")
        print(f"[AppliedAiProfessor.pause_for_questions] Questions: {questions}")
        unanswered_questions = [q for q in questions if not q['answered']]
        for question in unanswered_questions:
            answer = self.generate_text_response_for_question(question)
            response_audio_path = self.openai_wrapper.generate_audio(answer, "response.mp3", self.do_not_generate_audio)
            self.stream_audio_to_students(response_audio_path)
            question['answered'] = True  # Mark question as answered

        print("[AppliedAiProfessor.pause_for_questions] Resuming class...")

    def generate_text_response_for_question(self, question):
        print(
            f"[AppliedAiProfessor.generate_text_response_for_question] Student '{question['name']}' asked '{question['question']}'")
        answer = self.openai_wrapper.generate_response(question, self.do_not_generate_response)
        print(f"[AppliedAiProfessor.generate_text_response_for_question] Answer: {answer}")
        return answer

    def stream_audio_to_students(self, file_path):
        print(f"[AppliedAiProfessor.stream_audio_to_students] {file_path}")
        self.socketio.emit('next_audio_chunk', {'audioFile': file_path})  # Emit the next audio chunk

    def generate_audio_from_text(self, text, filename):
        print(f"[AppliedAiProfessor.generate_audio_from_text] Generating audio for text: {text}")
        return self.openai_wrapper.generate_audio(text, filename, self.do_not_generate_audio)
