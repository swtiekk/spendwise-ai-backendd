from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import sqlite3
import hashlib
import os

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

security = HTTPBearer()

# ── Pydantic Models (request bodies) ─────────────────────
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
        "docs": "http://127.0.0.1:8001/docs",
        "endpoints": [
            "POST /auth/register",
            "POST /auth/login",
            "GET  /expenses",
            "POST /expenses",
            "GET  /dashboard",
            "GET  /insights",
            "POST /smart-purchase",
            "GET  /categories",
            "GET  /alerts",
            "GET  /savings-goals",
        ]
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
        return {"message": "User registered successfully", "username": data.username, "email": data.email}
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
            "access_token": f"fastapi-token-{user['id']}-{data.username}",
            "token_type": "bearer"
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
            raise HTTPException(status_code=400, detail=f"Category '{data.category_key}' not found")

        cursor = db.execute(
            "INSERT INTO core_expense (amount, category_id, description, timestamp, created_at, updated_at, user_id) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), 3)",
            (data.amount, category["id"], data.description, data.timestamp)
        )
        db.commit()
        return {
            "id": cursor.lastrowid,
            "amount": data.amount,
            "category_key": data.category_key,
            "description": data.description,
            "timestamp": data.timestamp,
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

        breakdown = db.execute("""
            SELECT c.key, c.label, SUM(e.amount) as total
            FROM core_expense e
            LEFT JOIN core_category c ON e.category_id = c.id
            GROUP BY c.key, c.label
        """).fetchall()

        return {
            "total_expenses": total_expenses,
            "total_income": 18000.0,
            "balance": 18000.0 - total_expenses,
            "average_daily_spend": round(total_expenses / 30, 2),
            "category_breakdown": {r["key"]: float(r["total"]) for r in breakdown}
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
        income  = 18000.0
        balance = income - total_expenses

        safe_threshold    = balance * 0.10
        caution_threshold = balance * 0.25

        if balance <= 0:
            decision   = "risky"
            risk_score = 100
            reasoning  = f"Your current balance is ₱{balance:,.2f}. Any purchase right now is not recommended."
            suggestions = ["You have no remaining budget.", "Wait for your next income cycle."]
        elif amount <= safe_threshold:
            decision   = "safe"
            risk_score = int((amount / safe_threshold) * 30)
            reasoning  = f"₱{amount:,.2f} is within your safe spending range based on your balance of ₱{balance:,.2f}."
            suggestions = ["You can proceed.", "Log it immediately after buying."]
        elif amount <= caution_threshold:
            decision   = "caution"
            risk_score = int(30 + ((amount - safe_threshold) / (caution_threshold - safe_threshold)) * 40)
            reasoning  = f"₱{amount:,.2f} is manageable but will use a significant portion of your ₱{balance:,.2f} balance."
            suggestions = ["Only proceed if this is a priority.", "Look for a lower-cost alternative."]
        else:
            decision   = "risky"
            risk_score = min(100, int(70 + ((amount - caution_threshold) / caution_threshold) * 30))
            reasoning  = f"₱{amount:,.2f} exceeds 25% of your balance of ₱{balance:,.2f}."
            suggestions = ["Defer until next pay cycle.", "Review your spending breakdown first."]

        return {
            "decision":         decision,
            "risk_score":       risk_score,
            "reasoning":        reasoning,
            "suggestions":      suggestions,
            "current_balance":  balance,
            "remaining_budget": balance - amount,
            "safe_threshold":   safe_threshold,
            "caution_threshold": caution_threshold,
        }
    finally:
        db.close()

# ── Admin ─────────────────────────────────────────────────
@app.get("/admin/users")
def admin_users():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT u.id, u.username, u.email, u.first_name as name,
                   u.date_joined, p.income_type, p.income_cycle,
                   m.user_cluster as cluster, m.risk_level
            FROM auth_user u
            LEFT JOIN core_userprofile p ON u.id = p.user_id
            LEFT JOIN core_mlinsight m ON u.id = m.user_id
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()

@app.get("/admin/dashboard")
def admin_dashboard():
    db = get_db()
    try:
        total_users    = db.execute("SELECT COUNT(*) as c FROM auth_user").fetchone()["c"]
        total_expenses = db.execute("SELECT SUM(amount) as t FROM core_expense").fetchone()["t"] or 0
        clusters       = db.execute(
            "SELECT user_cluster, COUNT(*) as count FROM core_mlinsight GROUP BY user_cluster"
        ).fetchall()
        return {
            "total_users":          total_users,
            "total_expenses":       float(total_expenses),
            "cluster_distribution": {r["user_cluster"]: r["count"] for r in clusters}
        }
    finally:
        db.close()