from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Annotated
from datetime import datetime
from enum import Enum
import jwt

# WAITING FOR AI/ML TEAM
from ai_modules import sendGeminiMsg, readGeminiMsg

VERSION = "0.0.0"
SECRET_KEY = ""
origins = ["http://localhost:8000"]
ALGORITHM = "HS256"

app = FastAPI(title="VibeWealth API", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
#TEST DATABASE
DB_accounts = {}
DB_users = {}
DB_transactions = {}
DB_goals = {}

#ENUMS
class TransactionType(Enum, str):
    TO = "credit",
    FROM = "debit"

class GoalType(Enum, str):
    EDU = "educational"
    JOB = "occupational"
    PERSONAL = "personal"
    HOUSE = "housing"
    INSURANCE = "insurance"

class GoalLength(Enum, str):
    LONG = "long-term"
    INTERMEDIATE = "intermediate"
    SHORT = "short-term"

#CLASSES
class User(BaseModel):
    user_id: int
    name: str
    bal: int
    email: str
    password: str
    created_at: datetime

class NewAccount(BaseModel):
    acc_id: int
    name: str

class Account(BaseModel):
    acc_id: int
    user_id: int
    name: str
    bal: int
    created_at: datetime

class Transaction(BaseModel):
    trans_id: int
    acc_id: int
    amount: int
    trans_type: TransactionType
    created_at: datetime

class Goal(BaseModel):
    goal_id: int
    name: str
    desc: str | None
    user_id: int

@app.post("/auth/register")
def register(user_name: str, user_email: str):
    if user_email not in DB_users:
        return {"message": "E-mail already registered."}
    
    user_id = 0 # will use MongoDB built in user-id creator here.
    user = User(email=user_email, name=user_name, user_id = user_id, created_at = datetime.now())
    DB_users[user_email] = user
    
    access_token = jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.post("/auth/login", response_model=dict)
def login(user_email: str, user_password: str):
    if user_email not in DB_users:
        return {"message": "Invalid credentials"}
    
    user = DB_users[user_email]
    if user.password != user_password:  # In production, verify hashed password
        return {"message": "Invalid password"}
    
    access_token = jwt.encode({"sub": user.id}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer", "user": user.name}

@app.post("/accounts")
def create_account(new_acc: NewAccount, user_id: int):
    account = Account(
        acc_id = new_acc.acc_id,
        user_id = user_id,
        name = new_acc.name,
        bal = 0,
        created_at = datetime.now
    )
    DB_accounts[account.id] = account
    return account

@app.get("/accounts/")
def get_account(user_id: int):
    if(user_id not in DB_users):
        return {"message": "User not found."}
    
    accounts = [a for a in DB_accounts.values() if a.user_id == user_id]
    
    return accounts

@app.put("/accounts/{account_id}")
def edit_account(account_id: int, user_id: int, bal: int):
    if account_id not in DB_accounts:
        return {"message": "Account not found."}
    
    account = DB_accounts[account_id]
    if account.user_id != user_id:
        return {"message": "Access denied. Account does not belong to user."}

    account.bal = bal
    DB_accounts[account_id] = account
    return account

@app.delete("/accounts/{account_id}")
def delete_account(account_id: str, user_id: int):
    if account_id not in DB_accounts:
        return {"message": "Account not found."}
    
    account = DB_accounts[account_id]
    if account.user_id != user_id:
        return {"message": "Access denied. Account does not belong to user."}
    
    DB_accounts.pop(account_id)
    return {"message": "Account deleted successfully"}

@app.post("/transactions")
def create_transaction(transaction: Transaction, user_id: int):
    if transaction.acc_id not in DB_accounts:
        return {"message": "Account not found."}
    
    account = DB_accounts[transaction.acc_id]
    if account.user_id != user_id:
         return {"message": "Access denied. Account does not belong to user."}
    
    if transaction.trans_type == TransactionType.TO:
        account.bal += transaction.amount
    elif transaction.trans_type == TransactionType.FROM:
        account.bal -= transaction.amount

    DB_transactions[transaction.trans_id] = transaction
    DB_accounts[account.id] = account

    return transaction

@app.get("/transactions")
def get_transactions(user_id: int):
    if(user_id not in DB_users):
        return {"message": "User not found."}
    
    transactions = [t for t in DB_transactions.values() if DB_accounts[t.acc_id].user_id == user_id]
    
    return transactions

@app.post("/chatbot")
def send_message_to_chatbot(query: Annotated[str | None, Query(max_length=100)] = None):
    if not query:
        return {"message": "Please enter valid query to the chatbot."}
    
    #SEND TO QUERY TO AI MODEL HERE
    # sendGeminiMsg(query)

    return query

@app.get("/chatbot")
def read_message_from_chatbot():
    #READ MESSAGE HERE
    # readGeminiMsg()
    response = readGeminiMsg()
    return {"message": response}

@app.get("/goals")
def get_goals(user_id: int):
    if(user_id not in DB_users):
        return {"message": "User not found."}
    
    goals = [g for g in DB_goals if g.user_id == user_id]
    return goals

@app.post("/goals")
def create_goal(user_id: int, goal_name: str, goal_id: int, goal_desc: Annotated[str | None, Query(max_length=50)] = None):
    if(user_id not in DB_users):
        return {"message": "User not found."}
    
    goal = Goal(
        goal_id = goal_id,
        name = goal_name,
        user_id = user_id
    )
    
    if goal_desc:
        goal.desc = goal_desc

    DB_goals[goal.goal_id] = goal

    return goal
