# Approval Flow - Action Blocker as Central Authority

## Overview

All approval and rejection decisions are now handled by the **Action Blocker Service**. The Action Blocker is the central authority for all transaction approvals.

## Flow Diagram

```
1. User initiates transaction
   ↓
2. wallet-back calls action-blocker/api/check-transaction
   ↓
3. Action Blocker checks rules → flags if violations found
   ↓
4. Transaction stored in pending_transactions table (status: pending)
   ↓
5. Admin reviews in UI
   ↓
6. Admin clicks Approve/Reject
   ↓
7. wallet-back calls action-blocker/api/approve-transaction
   ↓
8. Action Blocker processes approval/rejection:
   - Updates pending_transactions status
   - If approved: Executes transaction (updates balances, creates record)
   - If rejected: Marks as rejected
   ↓
9. Returns result to wallet-back
   ↓
10. Frontend refreshes to show updated status
```

## API Endpoints

### Action Blocker Service

#### `POST /api/approve-transaction`
**Central authority for all approval decisions**

**Request:**
```json
{
  "transaction_id": "uuid",
  "approve": true/false,
  "reviewed_by": "admin-user-id",
  "review_notes": "optional notes"
}
```

**Response (Approved):**
```json
{
  "message": "Transaction approved and executed",
  "transaction_id": "executed-transaction-id",
  "status": "approved",
  "executed": true
}
```

**Response (Rejected):**
```json
{
  "message": "Transaction rejected",
  "status": "rejected",
  "executed": false
}
```

**What it does:**
1. Validates transaction exists and is pending
2. Updates `pending_transactions.status` to approved/rejected
3. If approved:
   - Validates sender has sufficient balance
   - Updates wallet balances
   - Creates transaction record
4. Returns result

#### `POST /api/check-transaction`
**Checks if transaction needs approval**

**Request:**
```json
{
  "from_user_id": "uuid",
  "to_user_id": "uuid",
  "amount": 100.0,
  "sender_balance": 500.0
}
```

**Response:**
```json
{
  "needs_approval": true/false,
  "violations": ["violation1", "violation2"],
  "approved": true/false
}
```

## Database Tables

### `pending_transactions`
Stores all flagged transactions awaiting approval:
- `id` - UUID primary key
- `from_user_id` - Sender UUID
- `to_user_id` - Recipient UUID
- `amount` - Transaction amount
- `status` - pending/approved/rejected
- `violations` - JSONB array of rule violations
- `created_at` - When transaction was flagged
- `reviewed_at` - When admin reviewed
- `reviewed_by` - Admin user ID
- `review_notes` - Optional notes

## Integration Points

### wallet-back Integration

**Before (Old Flow):**
- wallet-back handled approval logic
- Called action-blocker only for checking
- Executed transactions itself

**After (New Flow):**
- wallet-back delegates ALL approval decisions to action-blocker
- Calls `action-blocker/api/approve-transaction`
- Action Blocker handles execution

**Code in wallet-back:**
```python
# All approval decisions go through Action Blocker Service
action_blocker_url = os.getenv("ACTION_BLOCKER_URL")
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{action_blocker_url}/api/approve-transaction",
        json={
            "transaction_id": request.transaction_id,
            "approve": request.approve,
            "reviewed_by": user.id
        }
    )
    return response.json()
```

## Benefits

1. **Centralized Control**: All approval logic in one place
2. **Consistency**: Same approval logic for all transactions
3. **Audit Trail**: All decisions tracked in action-blocker
4. **Scalability**: Easy to add new approval rules
5. **Separation of Concerns**: wallet-back focuses on wallet operations, action-blocker handles security

## Error Handling

- **Action Blocker Down**: Returns 503 error, approval cannot proceed
- **Transaction Not Found**: Returns 404
- **Insufficient Balance**: Returns 400, transaction stays pending
- **Already Processed**: Returns success with current status

## Testing

Test the approval flow:
```bash
# Test approval endpoint
curl -X POST https://action-blocker.vercel.app/api/approve-transaction \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "your-transaction-id",
    "approve": true,
    "reviewed_by": "admin-user-id"
  }'
```

