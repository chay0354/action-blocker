"""
FastAPI wrapper for Action Blocker Service
Compatible with Vercel serverless functions
"""
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
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

app = FastAPI(title="Action Blocker API", redirect_slashes=False)

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client and rules engine lazily
supabase: Optional[Client] = None
rules_engine: Optional[RulesEngine] = None

def get_supabase() -> Client:
    """Get or initialize Supabase client"""
    global supabase
    if supabase is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_service_key:
            raise HTTPException(
                status_code=500,
                detail="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set as environment variables"
            )
        
        supabase = create_client(supabase_url, supabase_service_key)
    return supabase

def get_rules_engine() -> RulesEngine:
    """Get or initialize rules engine"""
    global rules_engine
    if rules_engine is None:
        supabase_client = get_supabase()
        rules_engine = RulesEngine(supabase_client)
    return rules_engine

# Request models
class TransactionCheckRequest(BaseModel):
    from_user_id: str
    to_user_id: str
    amount: float
    sender_balance: Optional[float] = 0

class ApproveTransactionRequest(BaseModel):
    transaction_id: str
    approve: bool
    reviewed_by: Optional[str] = None  # Admin user ID
    review_notes: Optional[str] = None

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
        engine = get_rules_engine()
        # Get active rules count
        active_rules = len([r for r in engine.rules if r.enabled])
        return {
            "status": "running",
            "running": True,
            "rules_count": len(engine.rules),
            "active_rules": active_rules
        }
    except HTTPException:
        raise
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
        engine = get_rules_engine()
        supabase_client = get_supabase()
        
        context = {
            "sender_balance": request.sender_balance,
            "supabase": supabase_client
        }
        
        transaction = {
            "from_user_id": request.from_user_id,
            "to_user_id": request.to_user_id,
            "amount": request.amount
        }
        
        needs_approval, violations = engine.check_transaction(transaction, context)
        
        return {
            "needs_approval": needs_approval,
            "violations": violations,
            "approved": not needs_approval
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/approve-transaction")
def approve_transaction(request: ApproveTransactionRequest):
    """
    Approve or reject a pending transaction
    This is the central authority for all approval decisions
    """
    try:
        supabase_client = get_supabase()
        
        # Get pending transaction
        pending_result = supabase_client.table("pending_transactions").select("*").eq(
            "id", request.transaction_id
        ).execute()
        
        if not pending_result.data or len(pending_result.data) == 0:
            raise HTTPException(status_code=404, detail="Pending transaction not found")
        
        pending_tx = pending_result.data[0]
        current_status = pending_tx.get("status", "pending")
        
        # Check if already processed
        if current_status == "approved" and request.approve:
            return {
                "message": "Transaction already approved",
                "status": "approved",
                "transaction_id": request.transaction_id
            }
        if current_status == "rejected" and not request.approve:
            return {
                "message": "Transaction already rejected",
                "status": "rejected"
            }
        
        if current_status != "pending":
            raise HTTPException(status_code=400, detail=f"Transaction is already {current_status}, cannot change status")
        
        # Update pending transaction status
        update_data = {
            "status": "approved" if request.approve else "rejected",
            "reviewed_at": datetime.utcnow().isoformat(),
            "reviewed_by": request.reviewed_by
        }
        if request.review_notes:
            update_data["review_notes"] = request.review_notes
        
        supabase_client.table("pending_transactions").update(update_data).eq(
            "id", request.transaction_id
        ).execute()
        
        # If approved, re-check rules and execute the transaction
        if request.approve:
            from_user_id = pending_tx["from_user_id"]
            to_user_id = pending_tx["to_user_id"]
            amount = float(pending_tx["amount"])
            
            # Get sender's wallet
            sender_wallet = supabase_client.table("wallets").select("balance").eq("user_id", from_user_id).execute()
            if not sender_wallet.data:
                # Update back to pending
                supabase_client.table("pending_transactions").update({
                    "status": "pending",
                    "violations": json.dumps(["Sender wallet not found"])
                }).eq("id", request.transaction_id).execute()
                raise HTTPException(status_code=400, detail="Sender wallet not found")
            
            sender_balance = float(sender_wallet.data[0]["balance"])
            
            # Re-check transaction against rules (Action Blocker validates again)
            engine = get_rules_engine()
            context = {
                "sender_balance": sender_balance,
                "supabase": supabase_client
            }
            
            transaction = {
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "amount": amount
            }
            
            needs_approval, violations = engine.check_transaction(transaction, context)
            
            # If rules still flag violations, admin can override, but we log it
            if needs_approval and violations:
                # Admin is explicitly approving despite violations - allow override
                # But we update violations to show current rule status
                print(f"⚠️  Admin approving transaction despite current violations: {violations}")
                # Update violations in pending_transactions to reflect current rule check
                supabase_client.table("pending_transactions").update({
                    "violations": json.dumps(violations)
                }).eq("id", request.transaction_id).execute()
            
            # Check if sender has sufficient balance
            if sender_balance < amount:
                # Update back to pending
                supabase_client.table("pending_transactions").update({
                    "status": "pending",
                    "violations": json.dumps([f"Insufficient balance: ${sender_balance:.2f} < ${amount:.2f}"])
                }).eq("id", request.transaction_id).execute()
                raise HTTPException(status_code=400, detail=f"Insufficient balance: ${sender_balance:.2f} < ${amount:.2f}")
            
            # Get recipient's wallet
            recipient_wallet = supabase_client.table("wallets").select("balance").eq("user_id", to_user_id).execute()
            recipient_balance = float(recipient_wallet.data[0]["balance"]) if recipient_wallet.data else 1000.0
            
            # Update balances
            new_sender_balance = sender_balance - amount
            new_recipient_balance = recipient_balance + amount
            
            supabase_client.table("wallets").update({"balance": new_sender_balance}).eq("user_id", from_user_id).execute()
            supabase_client.table("wallets").update({"balance": new_recipient_balance}).eq("user_id", to_user_id).execute()
            
            # Create transaction record
            transaction = supabase_client.table("transactions").insert({
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "amount": amount
            }).execute()
            
            return {
                "message": "Transaction approved and executed",
                "transaction_id": transaction.data[0]["id"] if transaction.data else None,
                "status": "approved",
                "executed": True
            }
        else:
            # Rejected
            return {
                "message": "Transaction rejected",
                "status": "rejected",
                "executed": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing approval: {str(e)}")

