# Action Blocker Service Configuration

## Service URL and Port

The Action Blocker Service runs on **port 8001** by default at **http://127.0.0.1:8001**

When you start the service, it will display:
```
📍 Service URL: http://127.0.0.1:8001
   Add this to wallet-back/.env: ACTION_BLOCKER_URL=http://127.0.0.1:8001
```

## Environment Variables

### For Action Blocker Service (`action-blocker/.env` or `wallet-back/.env`)

```env
# Host to bind the HTTP server (default: 127.0.0.1)
ACTION_BLOCKER_HOST=127.0.0.1

# Port for the HTTP API server (default: 8001)
ACTION_BLOCKER_PORT=8001

# Supabase credentials (can load from wallet-back/.env)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### For Backend (`wallet-back/.env`)

```env
# URL of the Action Blocker Service (if running standalone)
# This tells the backend where to find the external service
ACTION_BLOCKER_URL=http://127.0.0.1:8001

# Optional: If backend starts the service internally
ACTION_BLOCKER_HOST=127.0.0.1
ACTION_BLOCKER_PORT=8001
```

## Configuration Steps

### Option 1: Standalone Service (Recommended)

1. **Start the Action Blocker Service:**
   ```bash
   cd action-blocker
   python action_blocker_service.py
   ```
   
   You'll see:
   ```
   📍 Service URL: http://127.0.0.1:8001
   ```

2. **Add to `wallet-back/.env`:**
   ```env
   ACTION_BLOCKER_URL=http://127.0.0.1:8001
   ```

3. **Start the backend:**
   ```bash
   cd wallet-back
   python main.py
   ```

The backend will now connect to the external Action Blocker Service.

### Option 2: Internal Service (Started from Backend)

1. **Add to `wallet-back/.env`:**
   ```env
   ACTION_BLOCKER_HOST=127.0.0.1
   ACTION_BLOCKER_PORT=8001
   ```

2. **Start the backend:**
   ```bash
   cd wallet-back
   python main.py
   ```

3. **Start the service from Admin UI:**
   - Log in as admin
   - Click "Start" button in Admin Dashboard

## Changing the Port

If you want to use a different port:

1. **Set environment variable:**
   ```bash
   # Windows PowerShell
   $env:ACTION_BLOCKER_PORT="9000"
   
   # Linux/Mac
   export ACTION_BLOCKER_PORT=9000
   ```

2. **Or create `action-blocker/.env`:**
   ```env
   ACTION_BLOCKER_PORT=9000
   ```

3. **Update `wallet-back/.env`:**
   ```env
   ACTION_BLOCKER_URL=http://127.0.0.1:9000
   ```

## Service Endpoints

When running, the service exposes these HTTP endpoints:

- `GET http://127.0.0.1:8001/api/status` - Get service status
- `GET http://127.0.0.1:8001/health` - Health check
- `POST http://127.0.0.1:8001/api/stop` - Stop the service

## Verification

To verify the service is running:

```bash
# Check status
curl http://127.0.0.1:8001/api/status

# Or in browser
http://127.0.0.1:8001/api/status
```

You should see:
```json
{
  "status": "running",
  "running": true,
  "rules_count": 4,
  "active_rules": 4,
  "poll_interval": 2
}
```

