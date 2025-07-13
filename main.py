from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi import Depends
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sqlite3
import os
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "vani-expense-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

auth_scheme = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Serve frontend from /static/index.html at /
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_index():
    return FileResponse(os.path.join("static", "index.html"))


# Connect to file-based SQLite
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

# --- Create USERS table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")
    
# --- Create EXPENSES table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    category TEXT,
    note TEXT,
    user_id INTEGER,
    timestamp TEXT
)
""")

# Commit changes to DB
conn.commit()


class UserCreate(BaseModel):
    username: str
    password: str


@app.post("/register")
def register(user: UserCreate):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (user.username, user.password))
        conn.commit()
        return {"message": "User registered successfully!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists.")


class UserLogin(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(user: UserLogin):
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                   (user.username, user.password))
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401,
                            detail="Invalid username or password")

    user_id = row[0]
    token = create_access_token({"sub": user.username, "user_id": user_id})
    return {"access_token": token, "token_type": "bearer"}


# Model
class Expense(BaseModel):
    amount: float
    category: str
    note: Optional[str] = None


# Add expense
@app.post("/expenses/")
def add_expense(exp: Expense, user: dict = Depends(get_current_user)):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO expenses (amount, category, note, user_id, timestamp) VALUES (?, ?, ?, ?, ?)",
        (exp.amount, exp.category, exp.note, user["user_id"], timestamp))
    conn.commit()
    return {"message": "Expense added successfully!"}


# Get all expenses
@app.get("/expenses/")
def get_expenses(user: dict = Depends(get_current_user)):
    cursor.execute("SELECT * FROM expenses WHERE user_id = ?",
                   (user["user_id"], ))
    rows = cursor.fetchall()
    return [
        {
            "id": row[0],
            "amount": row[1],
            "category": row[2],
            "note": row[3],
            "timestamp": row[5]  # assuming column order
        } for row in rows
    ]


# Summary
@app.get("/summary/")
def get_summary():
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT category, SUM(amount) FROM expenses GROUP BY category")
    rows = cursor.fetchall()
    by_category = {category: amount for category, amount in rows}

    return {"total": total, "by_category": by_category}
