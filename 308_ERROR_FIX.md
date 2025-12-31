# 308 Error Fix Guide

## Problem
Getting "Action Blocker Service error: 308" when calling the action blocker from wallet-back.

## Root Cause
A 308 (Permanent Redirect) occurs when:
1. The URL has a **double slash** (`//`) in the path
2. The `ACTION_BLOCKER_URL` environment variable has incorrect formatting

## Test Results

✅ **Working URL formats:**
- `https://action-blocker.vercel.app/api/check-transaction` → 200 OK
- `https://action-blocker.vercel.app/api/status` → 200 OK

❌ **URLs that cause 308:**
- `https://action-blocker.vercel.app/api/check-transaction//` (double slash) → 308 Redirect

## Solution

### 1. Check Your Environment Variable

Make sure `ACTION_BLOCKER_URL` in your `wallet-back/.env` or Vercel environment variables is:

```env
ACTION_BLOCKER_URL=https://action-blocker.vercel.app
```

**NOT:**
- ❌ `https://action-blocker.vercel.app/` (trailing slash)
- ❌ `https://action-blocker.vercel.app//` (double slash)
- ❌ `https://action-blocker.vercel.app/api` (includes path)

### 2. The Code Already Handles This

The `wallet-back/main.py` code already:
- Strips trailing slashes: `action_blocker_url.rstrip('/')`
- Follows redirects: `follow_redirects=True`
- Constructs URLs correctly: `f"{action_blocker_url_clean}/api/check-transaction"`

### 3. Verify Your Deployment

**For Local Development:**
```bash
# Check your .env file
cat wallet-back/.env | grep ACTION_BLOCKER_URL
```

**For Vercel:**
1. Go to your Vercel project settings
2. Check Environment Variables
3. Ensure `ACTION_BLOCKER_URL` is set to: `https://action-blocker.vercel.app` (no trailing slash)

### 4. Test the Connection

Run the test script to verify:
```bash
cd action-blocker
python test_wallet_back_simulation.py
```

Expected output:
```
[SUCCESS] Request successful!
Status Code: 200
```

## Current Status

✅ The main Vercel URL (`https://action-blocker.vercel.app`) is working perfectly
✅ All endpoints return 200 OK
✅ Transaction checks work correctly

The 308 error is likely due to:
- Incorrect `ACTION_BLOCKER_URL` environment variable format
- Or using a preview/deployment URL that requires authentication

## Quick Fix

1. **Update your environment variable:**
   ```env
   ACTION_BLOCKER_URL=https://action-blocker.vercel.app
   ```

2. **Restart your wallet-back service**

3. **Test again**

