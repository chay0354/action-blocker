# Quick Start Guide

## What Port and Domain?

**Default Configuration:**
- **Host:** `127.0.0.1` (localhost)
- **Port:** `8001`
- **Full URL:** `http://127.0.0.1:8001`

When you start the service, it will show:
```
📍 Service URL: http://127.0.0.1:8001
   Add this to wallet-back/.env: ACTION_BLOCKER_URL=http://127.0.0.1:8001
```

## What to Add to `wallet-back/.env`

Add this line to your `wallet-back/.env` file:

```env
ACTION_BLOCKER_URL=http://127.0.0.1:8001
```

That's it! This tells the backend where to find the Action Blocker Service.

## Complete Setup

### Step 1: Start Action Blocker Service

```bash
cd action-blocker
python action_blocker_service.py
```

You'll see:
```
📍 Service URL: http://127.0.0.1:8001
   Add this to wallet-back/.env: ACTION_BLOCKER_URL=http://127.0.0.1:8001
```

### Step 2: Add to Backend .env

Edit `wallet-back/.env` and add:

```env
ACTION_BLOCKER_URL=http://127.0.0.1:8001
```

### Step 3: Start Backend

```bash
cd wallet-back
python main.py
```

The backend will now connect to the Action Blocker Service!

## Changing the Port

If you want to use a different port (e.g., 9000):

1. **Set environment variable before starting:**
   ```bash
   # Windows PowerShell
   $env:ACTION_BLOCKER_PORT="9000"
   python action_blocker_service.py
   
   # Linux/Mac
   export ACTION_BLOCKER_PORT=9000
   python action_blocker_service.py
   ```

2. **Update `wallet-back/.env`:**
   ```env
   ACTION_BLOCKER_URL=http://127.0.0.1:9000
   ```

## Verify It's Working

1. **Check service status:**
   ```bash
   curl http://127.0.0.1:8001/api/status
   ```

2. **Or in browser:**
   ```
   http://127.0.0.1:8001/api/status
   ```

3. **Check in Admin UI:**
   - Log in as admin
   - Look at the top right of Admin Dashboard
   - Should show "Action Blocker: Running" with green dot

## Summary

**Action Blocker Service:**
- Runs on: `http://127.0.0.1:8001` (default)
- Shows URL when started
- Exposes HTTP API for status checks

**Backend Configuration:**
- Add to `wallet-back/.env`: `ACTION_BLOCKER_URL=http://127.0.0.1:8001`
- Backend will automatically connect to the service

