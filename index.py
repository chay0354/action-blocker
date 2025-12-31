"""
FastAPI wrapper for Action Blocker Service
Compatible with Vercel serverless functions
"""
import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from rules_engine import RulesEngine
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = FastAPI(title="Action Blocker API")

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_service_key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

supabase: Client = create_client(supabase_url, supabase_service_key)

# Initialize rules engine
rules_engine = RulesEngine(supabase)

# Request models
class TransactionCheckRequest(BaseModel):
    from_user_id: str
    to_user_id: str
    amount: float
    sender_balance: Optional[float] = 0

@app.get("/")
def read_root():
    return {"message": "Action Blocker API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/status")
def get_status():
    """Get service status"""
    try:
        # Get active rules count
        active_rules = len([r for r in rules_engine.rules if r.enabled])
        return {
            "status": "running",
            "running": True,
            "rules_count": len(rules_engine.rules),
            "active_rules": active_rules
        }
    except Exception as e:
        return {
            "status": "error",
            "running": False,
            "error": str(e)
        }

@app.post("/api/check-transaction")
def check_transaction(request: TransactionCheckRequest):
    """Check if a transaction needs approval based on rules"""
    try:
        context = {
            "sender_balance": request.sender_balance,
            "supabase": supabase
        }
        
        transaction = {
            "from_user_id": request.from_user_id,
            "to_user_id": request.to_user_id,
            "amount": request.amount
        }
        
        needs_approval, violations = rules_engine.check_transaction(transaction, context)
        
        return {
            "needs_approval": needs_approval,
            "violations": violations,
            "approved": not needs_approval
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

