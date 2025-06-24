from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Annotated
from datetime import datetime
from enum import Enum

VERSION = "0.0.0"
API_KEY = ""
origins = ["http://localhost:8000"]

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

#ENUMS
class TransactionType(Enum):
    TO = "credit",
    FROM = "debit"

#CLASSES
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
