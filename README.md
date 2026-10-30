# SpendSense API

A lightweight REST API built with FastAPI and SQLite for tracking personal income/expenses, importing bank/UPI CSV statements, and flagging unusual spending.

## Features
- **JWT Auth:** User registration and login with bcrypt password hashing.
- **Transaction CRUD:** Add, filter (by category), and delete expenses or income records.
- **Bulk CSV Import:** Upload CSV statements (title, amount, category, tx_type) with automatic Pandas data cleaning for missing fields.
- **Spending Analytics:** Calculates net balance, category-wise breakdown, and flags anomalous expenses.

## Running Locally
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
