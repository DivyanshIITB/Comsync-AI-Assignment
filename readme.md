# 📞 Call Scheduler — Client & Server

This project implements a **Call Scheduling System** with a Flask backend and React frontend.  
Users can schedule or immediately initiate mock phone calls through an API.  
The backend handles job scheduling, persistence, and communication with the mock API,  
while the frontend provides a simple interface for managing and viewing scheduled calls.

---

---

## Setup Instructions

### 1. Backend Setup (Flask)

#### Prerequisites
- Python 3.8+
- `pip` installed

#### Steps
```bash
cd server
python -m venv venv
# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python app.py
```

Backend starts on:
👉 http://localhost:8000


----

## 2. Frontend Setup (React)
Prerequisites

Node.js 16+ and npm installed

Steps
``` bash
cd client
# Install dependencies
npm install

# Start the client, linking to backend
REACT_APP_BACKEND=http://localhost:8000 npm start
```

Frontend starts on:
👉 http://localhost:3000

----

## 3. Testing the Application

Open the frontend in your browser (http://localhost:3000).

Enter a phone number and optional schedule time.

Click Start Now (for immediate initiation) or Schedule (for future time).

View all scheduled and initiated calls in the list below.

The backend handles mock API interactions and updates statuses.

## Backend Design (Flask)

The backend (app.py) handles:


Scheduling of mock calls

Triggering calls at appropriate times

Storing and retrieving schedules in SQLite

Communicating with a mock external call API


## Frontend Design (React)

Simple UI built with React

Uses fetch to interact with backend REST APIs

Supports both "Start Now" and "Schedule Later" actions

Displays current status and external call ID for each entry

Automatically refreshes the schedule list after every operation

## A view of the frontend:
<img width="1913" height="1025" alt="image" src="https://github.com/user-attachments/assets/7192c252-4815-477a-bae5-0106229a2d41" />



## Design Decisions & Trade-offs:

| Aspect                     | Decision                                         | Trade-off                                                                                                       |
| -------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Database**               | Used SQLite for simplicity and local persistence | Not ideal for high concurrency or multi-user environments                                                       |
| **Scheduler**              | Used `APScheduler` for background job scheduling | Jobs do not persist if server restarts; a persistent queue (like Celery + Redis) would be better for production |
| **Mock API Calls**         | Used synchronous `requests` module               | Easier to implement, but blocks during API calls; async could improve scalability                               |
| **Frontend Communication** | Used REST over HTTP with CORS                    | Simpler than WebSockets, but not real-time; users must refresh or poll                                          |
| **Deployment Simplicity**  | Runs locally on `localhost` ports 3000/8000      | Easy for testing, not production-optimized                                                                      |
| **Error Handling**         | Wrapped API calls with minimal try/except blocks | Simple but lacks granular user feedback or retry logic                                                          |


## Tech Stack

Frontend: React (create-react-app)

Backend: Flask + SQLAlchemy + APScheduler

Database: SQLite (auto-generated)

API Integration: Mock API endpoints (POST and GET)

Language: Python, JavaScript (ES6)


