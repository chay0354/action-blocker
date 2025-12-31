# Standalone Action Blocker Service

The Action Blocker Service can now run as a **separate, independent service** that monitors transactions in real-time.

## Two Ways to Run

### Option 1: Run as Standalone Service (Recommended)

Run the service independently from the backend:

```bash
cd action-blocker
python action_blocker_service.py
```

Or use the simple starter:

```bash
python start_service.py
```

The service will:
- ✅ Load rules from database
- ✅ Monitor transactions continuously
- ✅ Log flagged transactions
- ✅ Run independently of the backend

### Option 2: Control from Admin UI

1. Start the backend server: `cd wallet-back && python main.py`
2. Log in as admin (`admin@admin`)
3. Go to Admin Dashboard
4. Click "Start" button next to "Action Blocker" status
5. The service will start and run in the background

## Service Features

- **Real-time Monitoring**: Checks transactions every 2 seconds
- **Rule Management**: Automatically reloads rules when updated
- **Independent Operation**: Runs separately from backend API
- **Status Monitoring**: Shows running status in admin dashboard
- **Graceful Shutdown**: Handles Ctrl+C and shutdown signals properly

## Status Indicators

- 🟢 **Green dot + "Running"**: Service is active and monitoring
- 🔴 **Red dot + "Stopped"**: Service is not running

## Service Output

When running, you'll see:
```
✅ Action Blocker Service initialized
   Loaded 4 rules
   - Amount Threshold: 🟢 Active
   - Repeated Transaction: 🟢 Active
   - High Frequency: 🟢 Active
   - Large Percentage: 🟢 Active
🔄 Action Blocker Service is running and monitoring transactions...
   Press Ctrl+C to stop
```

When it detects flagged transactions:
```
🚨 Flagged transaction detected:
   From: user-id-123
   To: user-id-456
   Amount: $600.00
   Violations: 1
      - Amount Threshold: Transaction amount $600.0 exceeds threshold of $500.0
```

## Stopping the Service

- **Standalone mode**: Press `Ctrl+C`
- **UI mode**: Click "Stop" button in admin dashboard

## Troubleshooting

### Service won't start?

1. Check `.env` file has `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
2. Verify database tables exist (run SQL script)
3. Check backend logs for errors

### Service not detecting transactions?

1. Make sure service is running (check status in UI)
2. Verify rules are enabled in Rules tab
3. Test with a transaction that should be flagged (> $500)

### Service stops unexpectedly?

1. Check database connection
2. Verify Supabase credentials are correct
3. Check for error messages in console


