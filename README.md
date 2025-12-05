Student Chatbot (AI in Web Assignment)

This project implements a full-stack AI-powered chatbot using FastAPI for the backend and Vite (HTML, CSS, JS) for the frontend.
It allows students to interact with a conversational AI model based on Google Gemini 2.5 Flash, providing accurate academic responses in real time.

 Project Overview
Backend (FastAPI)

Built with Python (FastAPI).

Uses Google Generative AI (Gemini 2.5 Flash) for natural language responses.

Exposes REST endpoints for communication with the frontend.

Fully containerized using Docker.

Frontend (Vite)

Developed using HTML, CSS, and JavaScript with Vite for fast builds.

Simple and responsive chat interface.

Connects to backend through HTTP API calls.

Project Structure
gemini-chatbot-docker/
│
├── backend/
│   ├── main.py               # FastAPI backend application
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Backend Docker build file
│   └── .env                  # Contains GEMINI_API_KEY
│
├── frontend/
│   ├── index.html            # Chat UI
│   ├── script.js             # Frontend logic for API calls
│   ├── vite.config.js        # Vite configuration
│   ├── Dockerfile            # Frontend Docker build file
│   └── package.json
│
└── docker-compose.yml        # Defines frontend & backend services

API Endpoints
Method	Endpoint	Description
GET	/health	Check if backend is running
POST	/v1/ai-student-qa	Send a question and receive AI response
Example Request
{
  "question": "What is Machine Learning?"
}

Example Response
{
  "answer": "Machine Learning is a subset of AI that enables systems to learn patterns from data and make predictions without explicit programming."
}

Running with Docker
1. Build and Start Containers
docker-compose up --build

2. Access the Services

Frontend: http://localhost:5173

Backend: http://localhost:8000

3. Verify Backend

Visit:

http://localhost:8000/health


Expected Response:

{ "status": "ok", "message": "Backend is running" }

Environment Variables

Create a .env file inside /backend with the following:

GEMINI_API_KEY=your_google_gemini_api_key

Technologies Used
Layer	Technology
Frontend	HTML, CSS, JavaScript, Vite
Backend	Python, FastAPI
AI Model	Google Gemini 2.5 Flash
Deployment	Docker & Docker Compose
Notes for Reviewers

The backend service is hosted locally via FastAPI inside the backend/ folder.

The frontend communicates with it using http://localhost:8000.

The file chat.db (if exists) stores simple chat logs but is optional.

The main backend logic is located in backend/main.py.