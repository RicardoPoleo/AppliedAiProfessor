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
        self.socketio.emit('start_class', {'audioFile': first_chunk})  # Emit start_class event to clients

    def get_next_chunk(self):
        print(f"[AppliedAiProfessor.get_next_chunk] Current chunk index: {len(self.chunks)}/{self.current_chunk_index}")
        if self.current_chunk_index < len(self.chunks):
            chunk_text = self.chunks[self.current_chunk_index]
            print(f"[AppliedAiProfessor.get_next_chunk] Chunk #{self.current_chunk_index + 1}. Text: '{chunk_text}'")
            audio_file = self.openai_wrapper.generate_audio(chunk_text,
                                                            f"speech_chunk_{self.current_chunk_index + 1}.mp3",
                                                            self.do_not_generate_audio)
            self.current_chunk_index += 1
            return os.path.basename(audio_file)  # Return only the filename
        else:
            return None

    def pause_for_questions(self):
        print("[AppliedAiProfessor.pause_for_questions] Pausing for questions...")
        questions = self.get_questions_from_users()
        for question in questions:
            print(f"[AppliedAiProfessor.pause_for_questions] Question received: {question}")
            answer = self.openai_wrapper.generate_response(question, self.do_not_generate_response)
            response_audio_path = self.openai_wrapper.generate_audio(answer, "response.mp3", self.do_not_generate_audio)
            self.stream_audio_to_students(response_audio_path)

        print("Resuming class...")

    def get_questions_from_users(self):
        # Implement a mechanism to receive text-based questions from users
        return ["Can you explain quadratic functions again?"]

    def stream_audio_to_students(self, file_path):
        print(f"[AppliedAiProfessor.stream_audio_to_students] {file_path}")
        self.socketio.emit('next_audio_chunk', {'audioFile': file_path})  # Emit the next audio chunk
