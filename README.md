# Transaction Blocker System

מערכת לזיהוי וחסימת פעולות חריגות במערכת הארנק הדיגיטלי.

## Overview

This system integrates with the existing wallet system to:
- Monitor all transactions in real-time
- Apply configurable rules to detect suspicious activity
- Flag transactions that violate rules for manual review
- Provide admin interface for reviewing and approving/rejecting flagged transactions

## Features

### Rules Engine
The system includes several built-in rules:

1. **Amount Threshold Rule**: Flags transactions above a certain amount (default: $500)
2. **Repeated Transaction Rule**: Flags if the same transaction repeats multiple times within a time window (default: 3 times in 10 minutes)
3. **High Frequency Rule**: Flags if a user makes too many transactions in a short time (default: 5 transactions in 5 minutes)
4. **Large Percentage Rule**: Flags if a transaction is a large percentage of user's balance (default: >50%)

### Database Tables

1. **pending_transactions**: Stores transactions flagged for review
   - Status: pending, approved, rejected
   - Violations: JSON array of rule violations
   - Review information: reviewed_by, reviewed_at, review_notes

2. **transaction_rules**: Stores rule configurations (optional, for future rule management UI)

## Setup

### 1. Database Setup

Run the SQL script to create the necessary tables:

```sql
-- Run this in your Supabase SQL editor
\i action-blocker/create_pending_transactions_table.sql
```

Or copy and paste the contents of `create_pending_transactions_table.sql` into the Supabase SQL editor.

### 2. Backend Integration

The rules engine is already integrated into `wallet-back/main.py`. The transfer endpoint now:
- Checks all transactions against rules before execution
- Creates pending transactions for flagged ones
- Only executes transactions after admin approval (if flagged)

### 3. Frontend Integration

The admin dashboard (`wallet-front/components/AdminDashboard.tsx`) now includes:
- A "Pending Review" tab showing all flagged transactions
- Violation details for each transaction
- Approve/Reject buttons with review notes
- Real-time updates when transactions are reviewed

## API Endpoints

### Admin Endpoints

- `GET /api/admin/pending-transactions` - Get all pending transactions
- `POST /api/admin/approve-transaction` - Approve or reject a pending transaction
  ```json
  {
    "transaction_id": "uuid",
    "approve": true/false,
    "review_notes": "optional notes"
  }
  ```
- `GET /api/admin/rules` - Get all active rules

## How It Works

1. **Transaction Initiation**: User attempts to transfer money
2. **Rule Checking**: System checks transaction against all active rules
3. **Decision**:
   - If no violations: Transaction executes immediately
   - If violations found: Transaction is saved to `pending_transactions` with status "pending"
4. **Admin Review**: Admin sees flagged transaction in dashboard
5. **Approval/Rejection**:
   - **Approve**: Transaction executes, moved to `transactions` table
   - **Reject**: Transaction marked as rejected, not executed

## Customizing Rules

Rules can be customized in `action-blocker/rules_engine.py`:

```python
# In RulesEngine._load_default_rules()
self.rules.append(AmountThresholdRule(threshold=1000.0))  # Change threshold
self.rules.append(RepeatedTransactionRule(max_repeats=5, time_window_minutes=15))  # Adjust parameters
```

## Future Enhancements

- Rule management UI for admins
- Rule configuration stored in database
- More rule types (geographic, time-based, etc.)
- Automated approval for trusted users
- Email notifications for flagged transactions
- Transaction history and analytics

## Files Structure

```
action-blocker/
├── rules_engine.py                    # Rules engine implementation
├── create_pending_transactions_table.sql  # Database schema
├── requirements.txt                    # Python dependencies
└── README.md                          # This file

wallet-back/
└── main.py                            # Updated with rules integration

wallet-front/
└── components/
    └── AdminDashboard.tsx            # Updated with pending transactions UI
```










