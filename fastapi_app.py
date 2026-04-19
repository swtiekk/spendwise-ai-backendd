from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import hashlib

app = FastAPI(title="SpendWise AI API", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database helper ───────────────────────────────────────
def get_db():
    db = sqlite3.connect('db.sqlite3')
    db.row_factory = sqlite3.Row
    return db

# ── Pydantic Models ───────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = ""

class LoginRequest(BaseModel):
    username: str
    password: str

class ExpenseRequest(BaseModel):
    amount: float
    category_key: str
    description: Optional[str] = ""
    timestamp: str

class SmartPurchaseRequest(BaseModel):
    amount: float
    category: str
    description: Optional[str] = ""

# ── Root ──────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "system": "SpendWise AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "http://127.0.0.1:8001/docs"
    }

# ── Auth ──────────────────────────────────────────────────
@app.post("/auth/register")
def register(data: RegisterRequest):
    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM auth_user WHERE username = ?", 
            (data.username,)
        ).fetchone()

        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

        hashed = hashlib.md5(data.password.encode()).hexdigest()

        db.execute(
            "INSERT INTO auth_user (username, email, first_name, password, is_active, is_staff, is_superuser, date_joined) VALUES (?, ?, ?, ?, 1, 0, 0, datetime('now'))",
            (data.username, data.email, data.first_name, hashed)
        )
        db.commit()

        return {
            "message": "User registered successfully",
            "username": data.username
        }

    finally:
        db.close()


@app.post("/auth/login")
def login(data: LoginRequest):
    db = get_db()
    try:
        user = db.execute(
            "SELECT * FROM auth_user WHERE username = ?",
            (data.username,)
        ).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "name": user["first_name"],
            },
            "token": f"fastapi-token-{user['id']}-{data.username}"
        }

    finally:
        db.close()

# ── Categories ────────────────────────────────────────────
@app.get("/categories")
def get_categories():
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM core_category").fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()

# ── Expenses ──────────────────────────────────────────────
@app.get("/expenses")
def get_expenses():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT e.id, e.amount, e.description, e.timestamp,
                   c.label as category_label, c.icon, c.color
            FROM core_expense e
            LEFT JOIN core_category c ON e.category_id = c.id
            ORDER BY e.timestamp DESC
        """).fetchall()

        return [dict(r) for r in rows]
    finally:
        db.close()


@app.post("/expenses")
def create_expense(data: ExpenseRequest):
    db = get_db()
    try:
        category = db.execute(
            "SELECT id FROM core_category WHERE key = ?",
            (data.category_key,)
        ).fetchone()

        if not category:
            raise HTTPException(status_code=400, detail="Category not found")

        cursor = db.execute(
            "INSERT INTO core_expense (amount, category_id, description, timestamp, created_at, updated_at, user_id) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), 3)",
            (data.amount, category["id"], data.description, data.timestamp)
        )

        db.commit()

        return {
            "id": cursor.lastrowid,
            "message": "Expense created successfully"
        }

    finally:
        db.close()

# ── Dashboard ─────────────────────────────────────────────
@app.get("/dashboard")
def get_dashboard():
    db = get_db()
    try:
        result = db.execute(
            "SELECT SUM(amount) as total FROM core_expense"
        ).fetchone()

        total_expenses = float(result["total"] or 0)

        return {
            "total_expenses": total_expenses,
            "total_income": 18000.0,
            "balance": 18000.0 - total_expenses
        }

    finally:
        db.close()

# ── Insights ──────────────────────────────────────────────
@app.get("/insights")
def get_insights():
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM core_mlinsight LIMIT 1"
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="No insights found")

        return dict(row)

    finally:
        db.close()

# ── Alerts ────────────────────────────────────────────────
@app.get("/alerts")
def get_alerts():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM core_alert ORDER BY created_at DESC"
        ).fetchall()

        return [dict(r) for r in rows]

    finally:
        db.close()

# ── Savings Goals ─────────────────────────────────────────
@app.get("/savings-goals")
def get_savings_goals():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM core_savingsgoal"
        ).fetchall()

        return [dict(r) for r in rows]

    finally:
        db.close()

# ── Smart Purchase ────────────────────────────────────────
@app.post("/smart-purchase")
def smart_purchase(data: SmartPurchaseRequest):
    amount = data.amount

    db = get_db()
    try:
        result = db.execute(
            "SELECT SUM(amount) as total FROM core_expense"
        ).fetchone()

        total_expenses = float(result["total"] or 0)
        income = 18000.0
        balance = income - total_expenses

        if balance <= 0:
            decision = "risky"
        elif amount <= balance * 0.10:
            decision = "safe"
        elif amount <= balance * 0.25:
            decision = "caution"
        else:
            decision = "risky"

        return {
            "decision": decision,
            "current_balance": balance
        }

    finally:
        db.close()