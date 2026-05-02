<div align="center">

# Student Chatbot — Powered by Gemini 2.5 Flash

**A full-stack, dockerized AI chatbot for academic Q&A, built with FastAPI and Vite.**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](#)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](#)
[![Gemini](https://img.shields.io/badge/Gemini_2.5-Flash-8E75B2?logo=googlegemini&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](#)

</div>

---

## Overview

A full-stack AI-powered chatbot designed for **students**, built as part of an "AI in Web" assignment. It combines a **FastAPI** Python backend with a **Vite** vanilla-JS frontend, both **fully containerized** with Docker Compose. The conversational layer is **Google Gemini 2.5 Flash**, surfaced through a simple REST API.

The point of the project: show that you can ship an LLM-backed product with proper separation of concerns, container orchestration, and a clean HTTP contract — not just call an API from a notebook.

---

## Architecture

```
┌────────────────────┐         ┌──────────────────────┐
│   Frontend (Vite)  │  HTTP   │   Backend (FastAPI)  │
│   localhost:5173   │◄───────►│   localhost:8000     │
│   HTML / CSS / JS  │         │   Python 3           │
└────────────────────┘         └──────────┬───────────┘
                                          │
                                          ▼
                               ┌──────────────────────┐
                               │  Google Gemini 2.5   │
                               │       Flash API      │
                               └──────────────────────┘
```

Both services are independent containers wired together by `docker-compose.yml`.

---

## Features

- **FastAPI backend** with health-check and Q&A endpoints
- **Vite frontend** — fast dev server, simple responsive chat UI
- **Gemini 2.5 Flash** integration via Google's Generative AI SDK
- **Docker Compose** — one command to start the entire stack
- **`.env`-based** API-key management (never committed)

---

## API Reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Service heartbeat |
| `POST` | `/v1/ai-student-qa` | Send a question, receive AI-generated answer |

**Request**
```json
{ "question": "What is Machine Learning?" }
```

**Response**
```json
{
  "answer": "Machine Learning is a subset of AI that enables systems to learn patterns from data and make predictions without explicit programming."
}
```

---

## Quick Start

```bash
git clone https://github.com/AlyLotfy/Gemini-Chatbot.git
cd Gemini-Chatbot
```

Create `backend/.env`:
```
GEMINI_API_KEY=your_google_gemini_api_key
```

Then build & start:
```bash
docker-compose up --build
```

- Frontend → http://localhost:5173
- Backend → http://localhost:8000
- Health  → http://localhost:8000/health

---

## Project Layout

```
gemini-chatbot-docker/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── requirements.txt     # Python deps
│   ├── Dockerfile
│   └── .env                 # GEMINI_API_KEY (gitignored)
├── frontend/
│   ├── index.html
│   ├── script.js            # API calls
│   ├── vite.config.js
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML / CSS / JavaScript · Vite |
| Backend | Python · FastAPI |
| AI Model | Google Gemini 2.5 Flash |
| Deployment | Docker · Docker Compose |

---

## Future Work

- Persist chat history in a real database (currently optional `chat.db`)
- Add streaming responses for snappier UX
- Add user accounts & per-user history
- Swap Gemini for a local Ollama model to remove the cloud dependency

---

## 📄 License

Academic project, AAST Computer Engineering.
