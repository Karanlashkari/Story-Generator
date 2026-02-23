# Story Generator Game

A high-performance backend for a captivating and interactive Story generation game, built using **FastAPI** and modern Python.

---

## Overview

**Story Generator Game** is a high-performance, asynchronous web application that serves as the backend for a real-time multiplayer game. It leverages the modern features of Python 3 and the FastAPI framework to provide a robust and scalable foundation for game development. This project is designed to handle multiple game sessions, player interactions, and game state management with ease.

The project is structured to support future expansion, additional game mechanics, and seamless frontend integration.

---

## Key Features

- **Asynchronous & High Performance**  
  Built on FastAPI with `async`/`await` to handle multiple concurrent players efficiently.
  
- **Scalable & Modular Design**  
  Clean separation of concerns for easy extension and maintenance.

- **Data Validation with Pydantic**  
  Ensures strict request and response validation for reliability.

- **Automatic API Documentation**  
  Swagger UI and ReDoc generated automatically.

- **Dockerized Setup**  
  Consistent development and deployment using Docker and Docker Compose.

---

## Tech Stack

### Backend
- **FastAPI** – High-performance asynchronous web framework
- **Python 3.10+** – Core programming language
- **Uvicorn** – ASGI server for FastAPI
- **Pydantic** – Data validation and serialization

## AI Integration

FastApiGame integrates **Large Language Models (LLMs)** to enhance gameplay by enabling intelligent, dynamic, and context-aware interactions.

- AI models are loaded from **Hugging Face**
- Models are used for:
  - Dynamic story or dialogue generation
  - Game event reasoning
  - Adaptive gameplay responses
- Inference is handled asynchronously to avoid blocking gameplay

The AI layer is designed to be modular, allowing easy replacement or upgrading of models.

### Frontend
- **React** – UI layer
- **Vite** – Frontend build tool

### DevOps / Tooling
- **Docker** – Containerized environment
- **Docker Compose** – Multi-service orchestration
- **Git & GitHub** – Version control and collaboration
