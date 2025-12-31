"""
Execute approved pending transactions that were marked as approved but not yet executed
This script will update balances and create transaction records
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def execute_approved_transactions(skip_confirm: bool = False):
    """Execute all approved pending transactions"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return
    
    print("="*70)
    print("EXECUTE APPROVED PENDING TRANSACTIONS")
    print("="*70)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Get all approved pending transactions
        result = supabase.table("pending_transactions").select("*").eq(
            "status", "approved"
        ).execute()
        
        approved = result.data if result.data else []
        
        if not approved:
            print("\n[OK] No approved transactions to execute")
            return
        
        print(f"\nFound {len(approved)} approved transactions to execute")
        
        # Display transactions
        for i, tx in enumerate(approved, 1):
            print(f"{i}. ID: {tx['id'][:8]}... | "
                  f"From: {tx['from_user_id'][:8]}... | "
                  f"To: {tx['to_user_id'][:8]}... | "
                  f"Amount: ${float(tx['amount']):.2f}")
        
        if not skip_confirm:
            confirm = input(f"\nExecute all {len(approved)} transactions? (yes/no): ")
            if confirm.lower() not in ['yes', 'y']:
                print("Cancelled.")
                return
        else:
            print(f"\nAuto-executing all {len(approved)} transactions (--yes flag set)...")
        
        print(f"\nExecuting {len(approved)} transactions...")
        print("-"*70)
        
        success_count = 0
        fail_count = 0
        
        for tx in approved:
            try:
                from_user_id = tx["from_user_id"]
                to_user_id = tx["to_user_id"]
                amount = float(tx["amount"])
                
                # Get sender's wallet
                sender_wallet = supabase.table("wallets").select("balance").eq(
                    "user_id", from_user_id
                ).execute()
                
                if not sender_wallet.data:
                    print(f"[ERROR] Sender wallet not found for transaction {tx['id'][:8]}...")
                    fail_count += 1
                    continue
                
                sender_balance = float(sender_wallet.data[0]["balance"])
                
                # Check if sender has enough balance
                if sender_balance < amount:
                    print(f"[ERROR] Insufficient balance for transaction {tx['id'][:8]}... "
                          f"(Balance: ${sender_balance:.2f}, Amount: ${amount:.2f})")
                    fail_count += 1
                    continue
                
                # Get recipient's wallet
                recipient_wallet = supabase.table("wallets").select("balance").eq(
                    "user_id", to_user_id
                ).execute()
                
                if not recipient_wallet.data:
                    print(f"[ERROR] Recipient wallet not found for transaction {tx['id'][:8]}...")
                    fail_count += 1
                    continue
                
                recipient_balance = float(recipient_wallet.data[0]["balance"])
                
                # Calculate new balances
                new_sender_balance = sender_balance - amount
                new_recipient_balance = recipient_balance + amount
                
                # Update balances
                supabase.table("wallets").update({
                    "balance": new_sender_balance
                }).eq("user_id", from_user_id).execute()
                
                supabase.table("wallets").update({
                    "balance": new_recipient_balance
                }).eq("user_id", to_user_id).execute()
                
                # Create transaction record
                supabase.table("transactions").insert({
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "amount": amount,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                
                print(f"[OK] Executed transaction {tx['id'][:8]}... "
                      f"(${amount:.2f} from {from_user_id[:8]}... to {to_user_id[:8]}...)")
                success_count += 1
                
            except Exception as e:
                print(f"[ERROR] Failed to execute transaction {tx['id'][:8]}...: {e}")
                fail_count += 1
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total transactions: {len(approved)}")
        print(f"Successfully executed: {success_count}")
        print(f"Failed: {fail_count}")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Execute approved pending transactions")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    execute_approved_transactions(skip_confirm=args.yes)

