# Approve All Pending Transactions Script

## Overview

This script allows you to approve or reject all pending transactions, even when the action blocker service is down or unavailable.

## Features

- ✅ Approve or reject all pending transactions
- ✅ Works even if action blocker service is down
- ✅ Two modes: API-based and direct database access
- ✅ Shows transaction details before approval
- ✅ Confirmation prompt before processing

## Setup

1. **Set environment variables** in `.env` file:

```env
# Required for API mode
WALLET_BACK_URL=http://127.0.0.1:8000
ADMIN_EMAIL=admin@admin
ADMIN_PASSWORD=admin123

# Required for direct DB mode
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

2. **Install dependencies** (if not already installed):

```bash
pip install httpx python-dotenv supabase
```

## Usage

### Method 1: API Mode (Recommended)

Uses the wallet-back API to approve transactions. This method:
- Respects all business logic
- Executes transactions properly
- Works even if action blocker is down (after fix)

```bash
# Approve all pending transactions
python approve_all_pending.py

# Reject all pending transactions
python approve_all_pending.py --reject
```

### Method 2: Direct Database Mode

Directly updates the database. Use this if:
- The wallet-back API is not available
- You need to bypass all checks
- You're doing bulk operations

```bash
# Approve all pending transactions (direct DB)
python approve_all_pending.py --direct-db
```

## How It Works

### API Mode

1. Authenticates as admin using Supabase Auth
2. Fetches all pending transactions via `/api/admin/pending-transactions`
3. Approves each transaction via `/api/admin/approve-transaction`
4. Shows progress and summary

### Direct DB Mode

1. Connects directly to Supabase database
2. Fetches all pending transactions
3. Updates status to "approved" or "rejected"
4. **Note:** This does NOT execute the transactions, only marks them as approved

## Important Notes

### Action Blocker Service Down

After the fix in `wallet-back/main.py`, transactions can now be approved even when the action blocker service is down. The system will:

1. Try to check with action blocker service
2. If service is unavailable (timeout/connection error), allow approval
3. If service returns an error status code, still block for safety

This ensures that:
- ✅ Transactions already flagged and stored can be approved by admin
- ✅ System remains functional even if action blocker service is down
- ✅ Safety checks still apply when service is available

### Transaction Execution

- **API Mode**: Transactions are fully executed (balances updated, transaction history created)
- **Direct DB Mode**: Only status is updated - transactions are NOT executed. You'll need to manually execute them or use the API mode.

## Example Output

```
======================================================================
APPROVE ALL PENDING TRANSACTIONS
======================================================================
Wallet Back URL: http://127.0.0.1:8000
Action: APPROVE
======================================================================
Authenticating as admin: admin@admin
✓ Authenticated as admin

Fetching pending transactions...
Found 3 pending transactions

Pending Transactions (3):
----------------------------------------------------------------------
1. ID: a1b2c3d4... | From: user1@example.com | To: user2@example.com | Amount: $600.00
   Violations: Amount exceeds threshold, Large percentage of balance
2. ID: e5f6g7h8... | From: user3@example.com | To: user4@example.com | Amount: $750.00
   Violations: Amount exceeds threshold
3. ID: i9j0k1l2... | From: user5@example.com | To: user6@example.com | Amount: $1200.00
   Violations: Amount exceeds threshold, High frequency detected

======================================================================
Are you sure you want to APPROVE all 3 transactions? (yes/no): yes

Processing 3 transactions...
----------------------------------------------------------------------
  ✓ Approved transaction a1b2c3d4...
  ✓ Approved transaction e5f6g7h8...
  ✓ Approved transaction i9j0k1l2...

======================================================================
SUMMARY
======================================================================
Total transactions: 3
Successfully approved: 3
Failed: 0
======================================================================
```

## Troubleshooting

### Authentication Failed

- Check `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`
- Verify admin user exists in Supabase
- Check Supabase credentials

### Cannot Connect to Wallet Back

- Ensure wallet-back is running
- Check `WALLET_BACK_URL` is correct
- Verify firewall/network settings

### Database Access Issues

- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Check RLS policies allow service role access
- Ensure `pending_transactions` table exists

## Related Files

- `wallet-back/main.py` - Contains the approve transaction endpoint
- `action-blocker/create_pending_transactions_table.sql` - Database schema

