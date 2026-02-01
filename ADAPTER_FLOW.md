# Action Blocker as Adapter - Simple Flow

## How It Works

The **Action Blocker acts as an adapter** that decides:
- ✅ **Auto-approve** if transaction passes all rules
- ⚠️ **Flag for review** if transaction violates rules

## Simple Step-by-Step

### Step 1: User Initiates Transaction
```
User → wallet-back → Action Blocker
```

### Step 2: Action Blocker Checks Rules
```
Action Blocker checks:
- Amount threshold
- Repeated transactions
- High frequency
- Large percentage
```

### Step 3: Action Blocker Decision

**Option A: No Violations (Clean Transaction)**
```
✅ Auto-approve
✅ Execute immediately:
   - Update balances
   - Create transaction record
✅ Return success to user
```

**Option B: Has Violations (Suspicious Transaction)**
```
⚠️ Flag for admin review
⚠️ Save to pending_transactions table
⚠️ Return "requires_approval: true" to user
```

### Step 4: Admin Reviews (Only if Flagged)
```
Admin sees pending transaction
Admin clicks Approve/Reject
→ Action Blocker processes approval
→ Executes if approved
```

## API Endpoints

### `POST /api/process-transaction`
**Main adapter endpoint - decides auto-approve or flag**

**Request:**
```json
{
  "from_user_id": "uuid",
  "to_user_id": "uuid",
  "amount": 100.0,
  "sender_balance": 500.0
}
```

**Response (Auto-approved):**
```json
{
  "message": "Transaction auto-approved and executed",
  "status": "approved",
  "auto_approved": true,
  "transaction_id": "uuid",
  "new_balance": 400.0,
  "requires_approval": false
}
```

**Response (Flagged for Review):**
```json
{
  "message": "Transaction flagged for review",
  "status": "pending",
  "auto_approved": false,
  "pending_transaction_id": "uuid",
  "violations": ["Amount Threshold: ..."],
  "requires_approval": true
}
```

### `POST /api/approve-transaction`
**For admin approval of flagged transactions**

**Request:**
```json
{
  "transaction_id": "uuid",
  "approve": true,
  "reviewed_by": "admin-user-id"
}
```

## Decision Logic

```
Transaction comes in
    ↓
Action Blocker checks rules
    ↓
┌─────────────────┬─────────────────┐
│  No Violations  │  Has Violations │
└─────────────────┴─────────────────┘
        ↓                    ↓
   Auto-approve        Flag for Review
   Execute now         Save to pending
   Return success      Wait for admin
```

## Benefits

1. **Smart Adapter**: Action Blocker makes all decisions
2. **Auto-approval**: Clean transactions execute immediately
3. **Safety**: Suspicious transactions always require review
4. **Centralized**: All logic in one place
5. **Flexible**: Easy to add new rules

## Example Scenarios

### Scenario 1: Clean Transaction ($50)
```
User sends $50
→ Action Blocker checks: No violations
→ Auto-approves and executes
→ User sees success immediately
```

### Scenario 2: Suspicious Transaction ($600)
```
User sends $600
→ Action Blocker checks: Violates amount threshold
→ Flags for review
→ Saves to pending_transactions
→ User sees "pending review" message
→ Admin reviews and approves
→ Action Blocker executes
```

## Key Point

**Action Blocker is the adapter:**
- ✅ Decides if transaction is good for rules
- ✅ Decides if it should auto-approve OR require admin review
- ✅ Executes clean transactions automatically
- ✅ Flags suspicious transactions for review

wallet-back just forwards requests - it doesn't make decisions.









