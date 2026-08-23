LocateMe-AI

AI-Based Missing Person Identification & CCTV Matching System

LocateMe-AI is an AI-powered missing person identification system that helps investigators register missing-person cases, process CCTV footage, detect faces, compare them against registered missing persons, and generate verification reports.

The system combines a FastAPI backend, computer vision, face embeddings, Supabase, and a Next.js command-center interface.

🚨 Problem Statement

Finding missing persons through large amounts of CCTV footage is a slow and highly manual process.

Investigators may need to:

Search through hours of CCTV footage

Identify faces manually

Compare possible matches with missing-person records

Track verification status

Maintain case information

Generate reports

LocateMe-AI automates this workflow by using face detection and face-embedding similarity matching to identify possible matches from CCTV footage.

🎯 Key Features

Missing Person Management

Register missing persons

Upload reference photographs

Generate face embeddings

Prevent duplicate case IDs

Detect duplicate face registrations

Search missing-person records

Filter cases by status

Update case status

CCTV Analysis

Upload CCTV video footage

Process video frames automatically

Sample frames at configurable intervals

Detect faces from CCTV frames

Compare detected faces with active missing-person embeddings

Record possible matches

Store matched CCTV frames

AI Face Matching

Face embedding generation

Cosine-similarity based matching

Configurable similarity threshold

Configurable high-confidence alert threshold

Multiple-face CCTV processing

Best-match selection

Verification Workflow

CCTV Match
    ↓
Pending Verification
    ↓
Operator Review
    ↓
Verify Match / Reject

This prevents an AI-generated match from automatically becoming a confirmed case.

Reports

Generate missing-person match reports

Include person details

Include case information

Include confidence score

Include CCTV information

Include verification status

Command Center

The Next.js frontend provides:

Dashboard

Missing Persons

Register Person

CCTV Analysis

Detection Results

Alerts

Analytics

Settings

🏗️ System Architecture

                    ┌─────────────────────┐
                    │     Next.js UI      │
                    │  Command Center     │
                    └──────────┬──────────┘
                               │
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI         │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ Face Engine │  │ Video       │  │ Matcher     │
       │             │  │ Processor   │  │             │
       └─────────────┘  └─────────────┘  └─────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │      Supabase       │
                    │ Database + Storage  │
                    └─────────────────────┘

🔄 Complete Workflow

Register Missing Person
        ↓
Upload Reference Photo
        ↓
Generate Face Embedding
        ↓
Store Person + Embedding
        ↓
Upload CCTV Video
        ↓
Extract Video Frames
        ↓
Detect Faces
        ↓
Generate Face Embeddings
        ↓
Compare With Registered Persons
        ↓
Similarity Threshold Check
        ↓
Possible Match
        ↓
Pending Verification
        ↓
Operator Verification
        ↓
Verified / Rejected
        ↓
Generate Match Report
        ↓
Update Alerts & Analytics

🧠 Face Matching

LocateMe-AI represents detected faces as numerical embeddings and compares CCTV embeddings against registered missing-person embeddings.

The similarity threshold is configurable through the Settings API.

Current configuration:

Similarity threshold : 0.70
Alert threshold      : 0.90
Frame sample interval: 1 second

The workflow separates AI detection from human verification.

A possible match does not automatically become a confirmed match.

🛠️ Technology Stack

Frontend

Next.js

React

TypeScript

Tailwind CSS

Backend

Python

FastAPI

Uvicorn

Computer Vision

OpenCV

NumPy

Pillow

Face embeddings

Database & Storage

Supabase

PostgreSQL

Supabase Storage

API

REST API

FastAPI Swagger / OpenAPI

📁 Project Structure

LocateMe-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── supabase_schema.sql
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   └── next.config.ts
│
├── docs/
├── DESIGN.md
├── README.md
└── .gitignore

🚀 Local Installation

Prerequisites

Install:

Python 3.10+

Node.js 20+

npm

Supabase project

1. Clone the Repository

git clone https://github.com/Kani2k06/LocateMe-AI.git
cd LocateMe-AI

⚙️ Backend Setup

cd backend

Create a virtual environment:

python -m venv .venv

Activate it:

.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Backend Environment Variables

Create:

backend/.env

Use backend/.env.example as the template.

Example:

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
STORAGE_DIR=storage
HOST=127.0.0.1
PORT=8000

Never commit real API keys or credentials.

Run Backend

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Backend:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

💻 Frontend Setup

Open another terminal:

cd frontend

Install dependencies:

npm install

Create:

frontend/.env.local

Configure the backend API URL according to your local setup.

Then run:

npm run dev

Frontend:

http://localhost:3000

🔌 API Modules

The backend provides endpoints for:

/api/health
/api/persons
/api/cctv
/api/detections
/api/alerts
/api/stats
/api/settings

Interactive API documentation is available through FastAPI Swagger.

🔐 Security

LocateMe-AI uses environment variables for sensitive configuration.

The repository intentionally excludes:

.env
.env.local
.venv
node_modules
.next
local storage
uploaded videos
generated images

Never expose Supabase secret/service credentials in the frontend.

📊 Verification Model

LocateMe-AI uses a human-in-the-loop verification workflow.

AI Detection
     ↓
Similarity Score
     ↓
Possible Match
     ↓
Human Verification
     ↓
Verified / Rejected

This approach helps reduce the risk of treating an uncertain AI prediction as a confirmed identification.

📄 Match Reports

Verified detections can be converted into downloadable match reports containing:

Missing person's name

Case ID

Verification status

Similarity/confidence score

Detection ID

CCTV location

Camera ID

Detection timestamp

Report generation timestamp

🧪 Testing

The system has been tested across the complete workflow:

Person Registration
        ✓
Face Embedding
        ✓
Duplicate Detection
        ✓
CCTV Upload
        ✓
Video Processing
        ✓
Face Detection
        ✓
Face Matching
        ✓
Detection Verification
        ✓
Alerts
        ✓
Analytics
        ✓
Match Report Generation
        ✓
Settings
        ✓

Frontend production build:

npm run build

Backend compilation:

python -m compileall app

🔮 Future Enhancements

Potential future improvements include:

Multi-camera live CCTV monitoring

Real-time streaming analysis

Advanced face tracking

Improved low-resolution face recognition

Role-based investigator accounts

Audit logs

Case collaboration

Mobile application

Cloud deployment

Larger-scale video processing

Advanced notification systems

👩‍💻 Author

Kanimozhi T

Artificial Intelligence & Machine Learning

GitHub:

https://github.com/Kani2k06