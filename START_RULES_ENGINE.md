# How to Start the Rules Engine

## Important: The Rules Engine is NOT a Standalone Service

The rules engine (`rules_engine.py`) is **NOT** meant to be run directly. It's a module that gets imported and used by the main backend server.

## How It Works

1. **The rules engine runs automatically** when you start the backend server
2. It loads rules from the database on startup
3. It checks every transaction in real-time as they come through the API

## To Start the System

### Step 1: Start the Backend Server

```bash
cd wallet-back
python main.py
```

When the backend starts, you should see output like:
```
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
Loaded 4 rules from database
```

The line "Loaded X rules from database" confirms the rules engine is running!

### Step 2: Verify It's Working

1. **Check the backend logs** - You should see "Loaded X rules from database" when it starts
2. **Make a test transaction** - Try transferring money that violates a rule (e.g., > $500)
3. **Check admin dashboard** - The transaction should appear in "Pending Review"

## How the Rules Engine Works

```
User tries to transfer money
    ↓
Backend receives request at /api/transfer
    ↓
Rules Engine checks transaction against all rules
    ↓
If violation found → Transaction goes to "Pending"
If no violation → Transaction executes immediately
```

## Troubleshooting

### Rules engine not loading?

1. **Check database connection** - Make sure Supabase credentials are correct in `.env`
2. **Check database tables** - Run `create_pending_transactions_table.sql` if you haven't
3. **Check backend logs** - Look for error messages when starting the server

### Rules not working?

1. **Verify rules are enabled** - Check in admin dashboard → Rules tab
2. **Check rule configuration** - Make sure thresholds are set correctly
3. **Test with a known violation** - Try transferring $600 (should trigger amount threshold rule)

## The Rules Engine is Always Running

Once the backend server is running, the rules engine is:
- ✅ **Active** - Checking every transaction
- ✅ **Listening** - Waiting for transactions to check
- ✅ **Updating** - Reloads rules when you change them in admin panel

You don't need to start it separately - it's part of the backend!

