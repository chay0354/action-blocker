# Transaction Blocker - Setup Instructions

## Quick Start

### 1. Create Database Tables

1. Open your Supabase Dashboard
2. Go to SQL Editor
3. Copy and paste the contents of `create_pending_transactions_table.sql`
4. Run the SQL script

This will create:
- `pending_transactions` table for flagged transactions
- `transaction_rules` table for rule management (optional)

### 2. Restart Backend Server

The backend (`wallet-back/main.py`) has been updated with the rules engine integration. Restart your backend server:

```bash
cd wallet-back
python main.py
```

### 3. Frontend is Ready

The admin dashboard has been updated with the pending transactions review interface. No additional setup needed.

## Testing the System

### Test Scenario 1: Amount Threshold

1. Log in as a regular user
2. Try to transfer more than $500
3. The transaction should be flagged
4. Log in as admin (`admin@admin`)
5. Go to Admin Dashboard → "Pending Review" tab
6. You should see the flagged transaction with violations
7. Click "Review Transaction" and approve/reject it

### Test Scenario 2: Repeated Transactions

1. Log in as a regular user
2. Make the same transaction (same recipient, same amount) 3 times within 10 minutes
3. The 3rd transaction should be flagged
4. Check admin dashboard for pending transaction

### Test Scenario 3: High Frequency

1. Log in as a regular user
2. Make 5 different transactions within 5 minutes
3. The 5th transaction should be flagged
4. Check admin dashboard

### Test Scenario 4: Large Percentage

1. Log in as a regular user
2. Check your balance
3. Transfer more than 50% of your balance
4. Transaction should be flagged
5. Check admin dashboard

## Default Rules

The system comes with 4 default rules:

1. **Amount Threshold**: Flags transactions > $500
2. **Repeated Transaction**: Flags if same transaction repeats 3+ times in 10 minutes
3. **High Frequency**: Flags if user makes 5+ transactions in 5 minutes
4. **Large Percentage**: Flags if transaction > 50% of user balance

## Customizing Rules

Edit `action-blocker/rules_engine.py` and modify the `_load_default_rules()` method:

```python
def _load_default_rules(self):
    # Change threshold to $1000
    self.rules.append(AmountThresholdRule(threshold=1000.0))
    
    # Change repeated transaction rule
    self.rules.append(RepeatedTransactionRule(max_repeats=5, time_window_minutes=15))
    
    # Add more rules...
```

Then restart the backend server.

## Troubleshooting

### Transactions not being flagged

1. Check that `pending_transactions` table exists in database
2. Check backend logs for errors
3. Verify rules are enabled (check `rules_engine.py`)

### Admin can't see pending transactions

1. Verify you're logged in as `admin@admin`
2. Check browser console for API errors
3. Verify backend is running and accessible
4. Check that `/api/admin/pending-transactions` endpoint is working

### Rules not working

1. Check backend logs for rule engine errors
2. Verify Supabase connection is working
3. Check that transaction data is being passed correctly to rules engine

## API Testing

You can test the API endpoints directly:

```bash
# Get pending transactions
curl -X GET "http://127.0.0.1:8000/api/admin/pending-transactions" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Approve a transaction
curl -X POST "http://127.0.0.1:8000/api/admin/approve-transaction" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "PENDING_TX_ID",
    "approve": true,
    "review_notes": "Looks good"
  }'
```

## Next Steps

- Customize rules for your use case
- Add more rule types as needed
- Consider adding email notifications
- Build rule management UI (optional)


