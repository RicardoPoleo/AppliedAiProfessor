import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.get_env("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def load_script_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def split_text(text, chunk_size=40):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

script_file_path = "path_to_your_script_file.txt"
script = load_script_from_file(script_file_path)

# Split the script into chunks
chunks = split_text(script)

for i, chunk in enumerate(chunks):
    print(f"Generating audio for chunk {i + 1}/{len(chunks)}")
    print(chunk)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=chunk
    )
    speech_file_path = f"/content/speech_chunk_{i + 1}.mp3"
    response.stream_to_file(speech_file_path)
    print(f"Saved: {speech_file_path}")


script = """
Hello everyone! Welcome to the first class of MATH 201: Elementary Functions. I am your instructor, Applied AI Professor, and I am thrilled to have you all here today. This class will be an exciting exploration of fundamental functions in mathematics. Before we dive into the content, I want to give you some important details about the course and how we will work together throughout the semester.

Let's start with some information about myself and how you can contact me. If you have any questions or need additional help, you can reach me via email at applied.ai@georgebrown.ca. Additionally, if you ever want to speak with me in person, I will be available at the Casa Loma campus in Toronto. We don't have a phone number for this course, so email will be our primary mode of communication.

To ensure everyone has the opportunity to get the help they need, I have set office hours from Monday to Friday, 2 to 4 pm. During this time, I will be available to answer your questions and help with any course-related topics. Don't hesitate to email me to schedule a meeting if needed.

Now, let's talk about the course overview, starting with the course objectives. Our main goal in MATH 201 is to understand and apply fundamental concepts of functions. By the end of the course, you should be able to:

Graph equations and understand the relationships between variables.
Work with different types of functions, including linear, quadratic, exponential, and logarithmic.
Solve problems using functions and their transformations.
Apply these concepts in broader contexts within mathematics and science.
For this course, we will use the "Math 201 Guide". This material is essential for your success in the course and will be sent to you via email or can be downloaded from the course's official website. Make sure to have it accessible for each class and for your personal study.
"""

# Function to split text into chunks of ~30-40 words
def split_text(text, chunk_size=40):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

# Split the script into chunks
chunks = split_text(script)

for i, chunk in enumerate(chunks):
    print(f"Generating audio for chunk {i + 1}/{len(chunks)}")
    print(chunk)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=chunk
    )
    speech_file_path = f"/content/speech_chunk_{i + 1}.mp3"
    response.stream_to_file(speech_file_path)
    print(f"Saved: {speech_file_path}")