# Expense Tracker – FastAPI App

A multi-user expense tracker built with **FastAPI**, **SQLite**, and vanilla **HTML/CSS/JS**. Users can register, log in securely with JWT, and manage expenses with category-wise summaries and timestamps.

---

## Features
- JWT-based user login & registration
- Add, view, and summarize expenses
- Auto timestamp per expense
- Responsive UI with styled login/register pages

---

## Tech Stack
- FastAPI + Python
- SQLite (file-based DB)
- HTML/CSS/JS (frontend)
- JWT auth with `python-jose`

---

## Demo
Watch Demo -(https://github.com/vaani68/expense_tracker.fastapi/blob/main/Demo.mp4) 

---

## Run Locally

```bash
git clone https://github.com/vaani68/expense_tracker.fastapi.git
cd expense_tracker.fastapi
pip install -r requirements.txt
uvicorn main:app --reload
