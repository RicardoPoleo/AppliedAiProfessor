### README

# Applied AI Professor

This project uses

This project integrates OpenAI's GPT-4o, Text-to-Speech (TTS) and Speech-to-Text to create an interactive AI system 
for giving classes to conversations. It combines visual and audio inputs for a seamless user experience.

This project simulates a real class experience on Zoom or any other tool used for  a class session using AI 
to generate responses and audio for student questions. It uses Flask for the backend, Flask-SocketIO for real-time communication, and the OpenAI API for text and audio generation.

## Tech Stack

- **Backend**:
  - **Python**: Main programming language.
  - **Flask**: Web framework.
  - **Flask-SocketIO**: WebSocket communication.
  - **OpenAI API**: Text and audio generation.
- **Frontend**:
  - **HTML/CSS**: Page structure and styling.
  - **JavaScript**: Client-side scripting.
  - **Socket.IO**: Real-time communication.
  - **Bootstrap**: Responsive design.

## Project Architecture

### Backend Components

- **Flask**: Web framework for handling HTTP routes.
- **Flask-SocketIO**: WebSocket communication for real-time features.
- **OpenAI API**: Text and audio generation.

### Key Files

- **`OpenAIWrapper.py`**: Interacts with OpenAI API.
- **`AppliedAIProfessor.py`**: Simulates class sessions and handles student interactions.
- **`backend.py`**: Backend server handling HTTP routes and WebSocket events.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/applied-ai-professor.git
    cd applied-ai-professor
    ```

2. **Create a virtual environment**:
    ```sh
    python -m venv venv
    ```

3. **Activate the virtual environment**:
    - On Windows:
        ```sh
        venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```sh
        source venv/bin/activate
        ```

4. **Install the required packages**:
    ```sh
    pip install -r requirements.txt
    ```

5. **Set up environment variables**:
    - Create a `.env` file in the root directory of the project.
    - Add your OpenAI API key to the `.env` file:
        ```
        OPENAI_API_KEY=your_openai_api_key
        ```

### Running the Project

1. **Run the backend server**:
    ```sh
    python backend.py
    ```

2. **Access the application**:
    - Open your web browser and go to `http://localhost:5000` for the student page.
    - Go to `http://localhost:5000/admin` for the admin page.

### Usage

- **Start Class**: Initiate a class session.
- **Submit Question**: Students can submit questions during the class.
- **Pause Class**: Pause the class to handle pending questions.
- **Resume Class**: Resume the class session.
- **End Class**: End the class session.

### Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a pull request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.