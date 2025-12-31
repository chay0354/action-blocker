# Action Blocker Flow Chart

## Simple Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INITIATES TRANSACTION                    │
│                    (Sends money to someone)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WALLET-BACK RECEIVES                       │
│                   (Validates user, balance)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              CALLS: action-blocker/api/process-transaction      │
│              (Sends: from_user_id, to_user_id, amount)         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ACTION BLOCKER CHECKS RULES                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ✓ Amount Threshold?  (e.g., > $500)                    │  │
│  │  ✓ Repeated Transaction?  (same tx 3+ times)             │  │
│  │  ✓ High Frequency?  (5+ tx in 5 minutes)                 │  │
│  │  ✓ Large Percentage?  (>50% of balance)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────┐      ┌───────────────────┐
    │  NO VIOLATIONS   │      │  HAS VIOLATIONS   │
    │  (Clean Transaction)    │  (Suspicious Transaction)
    └──────────┬────────┘      └──────────┬────────┘
               │                          │
               ▼                          ▼
    ┌───────────────────┐      ┌───────────────────┐
    │  AUTO-APPROVE     │      │  FLAG FOR REVIEW  │
    │                   │      │                   │
    │  ✓ Update balances│      │  ✓ Save to        │
    │  ✓ Create record  │      │     pending_      │
    │  ✓ Return success │      │     transactions  │
    │                   │      │  ✓ Return         │
    │                   │      │     "pending"     │
    └──────────┬────────┘      └──────────┬────────┘
               │                          │
               │                          │
               ▼                          ▼
    ┌───────────────────┐      ┌───────────────────┐
    │  USER SEES        │      │  USER SEES        │
    │  "Success!"       │      │  "Pending Review" │
    └───────────────────┘      └──────────┬────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │  ADMIN REVIEWS IN UI   │
                              │  (Sees violations)     │
                              └──────────┬─────────────┘
                                         │
                                         ▼
                              ┌────────────────────────┐
                              │  ADMIN CLICKS APPROVE  │
                              └──────────┬─────────────┘
                                         │
                                         ▼
                              ┌────────────────────────┐
                              │  ACTION BLOCKER        │
                              │  /api/approve-transaction│
                              │  ✓ Updates status      │
                              │  ✓ Executes transaction│
                              └──────────┬─────────────┘
                                         │
                                         ▼
                              ┌────────────────────────┐
                              │  TRANSACTION COMPLETE  │
                              └────────────────────────┘
```

## Decision Points

### Decision 1: Action Blocker Checks Rules
```
Transaction Data
    ↓
Check Rules:
    • Amount > $500? → Violation
    • Same tx 3+ times? → Violation
    • 5+ tx in 5 min? → Violation
    • Amount > 50% balance? → Violation
    ↓
Any Violations?
    ├─ NO  → Auto-Approve Path
    └─ YES → Flag for Review Path
```

### Decision 2: Auto-Approve Path (No Violations)
```
Clean Transaction
    ↓
Action Blocker:
    1. Updates sender balance (-amount)
    2. Updates recipient balance (+amount)
    3. Creates transaction record
    ↓
Returns Success
    ↓
User sees "Transfer successful"
```

### Decision 3: Flag for Review Path (Has Violations)
```
Suspicious Transaction
    ↓
Action Blocker:
    1. Saves to pending_transactions
    2. Status = "pending"
    3. Stores violations list
    ↓
Returns "Pending Review"
    ↓
User sees "Transaction flagged for review"
    ↓
Admin reviews in UI
    ↓
Admin approves/rejects
    ↓
Action Blocker executes if approved
```

## Complete Flow Summary

```
START: User sends money
    ↓
wallet-back validates
    ↓
Action Blocker checks rules
    ↓
    ├─ Clean? → Auto-execute → DONE
    └─ Violations? → Flag → Admin reviews → Execute → DONE
```

## Key Points

1. **Action Blocker is the adapter** - makes all decisions
2. **Clean transactions** - execute immediately (no admin needed)
3. **Suspicious transactions** - always require admin review
4. **All execution** - happens in Action Blocker (not wallet-back)

