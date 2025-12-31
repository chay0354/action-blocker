"""
Script to approve all pending transactions
Works even if the action blocker service is down
"""
import os
import sys
import httpx
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configuration
WALLET_BACK_URL = os.getenv("WALLET_BACK_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Supabase credentials (for direct database access if needed)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

async def get_admin_token():
    """Get admin authentication token"""
    print(f"Authenticating as admin: {ADMIN_EMAIL}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Try to login via Supabase Auth
            # First, get the Supabase URL
            if not SUPABASE_URL:
                raise ValueError("SUPABASE_URL not set")
            
            supabase_auth_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
            
            response = await client.post(
                supabase_auth_url,
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                },
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                print(f"Auth failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"Error getting admin token: {e}")
        return None

async def get_pending_transactions(token: str):
    """Get all pending transactions"""
    print("\nFetching pending transactions...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WALLET_BACK_URL.rstrip('/')}/api/admin/pending-transactions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                pending = data.get("pending_transactions", [])
                print(f"Found {len(pending)} pending transactions")
                return pending
            else:
                print(f"Error fetching pending transactions: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
    except httpx.ConnectError:
        print(f"Error: Cannot connect to wallet-back at {WALLET_BACK_URL}")
        print("Make sure wallet-back is running!")
        return []
    except Exception as e:
        print(f"Error fetching pending transactions: {e}")
        return []

async def approve_transaction(token: str, transaction_id: str, approve: bool = True):
    """Approve or reject a transaction"""
    action = "approve" if approve else "reject"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WALLET_BACK_URL.rstrip('/')}/api/admin/approve-transaction",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "transaction_id": transaction_id,
                    "approve": approve
                },
                timeout=30.0  # Longer timeout in case action blocker is slow
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ {action.capitalize()}d transaction {transaction_id[:8]}...")
                if "violations" in data and data.get("status") == "blocked":
                    print(f"    ⚠️  Warning: Transaction still blocked by rules")
                return True
            else:
                print(f"  ✗ Failed to {action} transaction {transaction_id[:8]}...: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                return False
                
    except httpx.TimeoutException:
        print(f"  ✗ Timeout while trying to {action} transaction {transaction_id[:8]}...")
        return False
    except Exception as e:
        print(f"  ✗ Error {action}ing transaction {transaction_id[:8]}...: {e}")
        return False

async def approve_all_pending(approve: bool = True):
    """Approve or reject all pending transactions"""
    action = "approve" if approve else "reject"
    
    print("="*70)
    print(f"APPROVE ALL PENDING TRANSACTIONS")
    print("="*70)
    print(f"Wallet Back URL: {WALLET_BACK_URL}")
    print(f"Action: {action.upper()}")
    print("="*70)
    
    # Get admin token
    token = await get_admin_token()
    if not token:
        print("\n❌ Failed to authenticate as admin")
        print("Make sure ADMIN_EMAIL and ADMIN_PASSWORD are set correctly")
        return
    
    print("✓ Authenticated as admin")
    
    # Get pending transactions
    pending = await get_pending_transactions(token)
    
    if not pending:
        print("\n✓ No pending transactions to process")
        return
    
    # Display pending transactions
    print(f"\nPending Transactions ({len(pending)}):")
    print("-"*70)
    for i, tx in enumerate(pending, 1):
        violations = tx.get("violations", [])
        violations_str = ", ".join(violations[:2]) if violations else "None"
        if len(violations) > 2:
            violations_str += f" (+{len(violations)-2} more)"
        
        print(f"{i}. ID: {tx['id'][:8]}... | "
              f"From: {tx.get('from_user_email', tx['from_user_id'][:8])} | "
              f"To: {tx.get('to_user_email', tx['to_user_id'][:8])} | "
              f"Amount: ${tx['amount']:.2f}")
        if violations:
            print(f"   Violations: {violations_str}")
    
    # Confirm action
    print("\n" + "="*70)
    if approve:
        confirm = input(f"Are you sure you want to APPROVE all {len(pending)} transactions? (yes/no): ")
    else:
        confirm = input(f"Are you sure you want to REJECT all {len(pending)} transactions? (yes/no): ")
    
    if confirm.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Process all transactions
    print(f"\nProcessing {len(pending)} transactions...")
    print("-"*70)
    
    success_count = 0
    fail_count = 0
    
    for tx in pending:
        success = await approve_transaction(token, tx['id'], approve)
        if success:
            success_count += 1
        else:
            fail_count += 1
        await asyncio.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total transactions: {len(pending)}")
    print(f"Successfully {action}d: {success_count}")
    print(f"Failed: {fail_count}")
    print("="*70)

async def approve_all_direct_db():
    """Approve all pending transactions directly via database (bypasses action blocker check)"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set for direct DB access")
        return
    
    print("="*70)
    print("APPROVE ALL PENDING TRANSACTIONS (Direct Database)")
    print("="*70)
    print("⚠️  This bypasses the action blocker service check")
    print("="*70)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Get all pending transactions
        result = supabase.table("pending_transactions").select("*").eq(
            "status", "pending"
        ).execute()
        
        pending = result.data if result.data else []
        
        if not pending:
            print("\n✓ No pending transactions found")
            return
        
        print(f"\nFound {len(pending)} pending transactions")
        
        # Display transactions
        for i, tx in enumerate(pending, 1):
            print(f"{i}. ID: {tx['id'][:8]}... | "
                  f"Amount: ${float(tx['amount']):.2f} | "
                  f"Created: {tx.get('created_at', 'N/A')}")
        
        # Confirm
        confirm = input(f"\nApprove all {len(pending)} transactions? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
        
        # Update all to approved
        for tx in pending:
            supabase.table("pending_transactions").update({
                "status": "approved",
                "reviewed_at": datetime.utcnow().isoformat(),
                "reviewed_by": None  # Script approval
            }).eq("id", tx["id"]).execute()
            print(f"✓ Approved transaction {tx['id'][:8]}...")
        
        print(f"\n✓ Successfully approved {len(pending)} transactions")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Approve or reject all pending transactions")
    parser.add_argument("--reject", action="store_true", help="Reject instead of approve")
    parser.add_argument("--direct-db", action="store_true", help="Use direct database access (bypasses action blocker)")
    
    args = parser.parse_args()
    
    if args.direct_db:
        asyncio.run(approve_all_direct_db())
    else:
        asyncio.run(approve_all_pending(approve=not args.reject))

