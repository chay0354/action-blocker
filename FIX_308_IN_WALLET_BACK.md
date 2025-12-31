# Fix for 308 Error in wallet-back

## Problem
Even with `follow_redirects=True`, httpx sometimes returns a 308 status code instead of following the redirect automatically.

## Solution
Add explicit handling for 308 redirects in `wallet-back/main.py`.

## Code Changes Needed

In `wallet-back/main.py`, update the action blocker service call sections to explicitly handle 308 redirects:

### Location 1: Transfer endpoint (around line 324-353)

Replace:
```python
async with httpx.AsyncClient(follow_redirects=True) as client:
    check_response = await client.post(
        f"{action_blocker_url_clean}/api/check-transaction",
        json={...},
        timeout=5.0
    )
    
    if check_response.status_code == 200:
        ...
    elif check_response.status_code == 503:
        ...
    else:
        violations = [f"Action Blocker Service error: {check_response.status_code}"]
```

With:
```python
async with httpx.AsyncClient(follow_redirects=True) as client:
    check_response = await client.post(
        f"{action_blocker_url_clean}/api/check-transaction",
        json={...},
        timeout=10.0  # Increased timeout
    )
    
    # Handle 308 redirects explicitly
    if check_response.status_code == 308:
        location = check_response.headers.get('Location')
        if location:
            # Follow the redirect manually
            if location.startswith('/'):
                redirect_url = f"{action_blocker_url_clean}{location}"
            elif not location.startswith('http'):
                redirect_url = f"{action_blocker_url_clean}/{location}"
            else:
                redirect_url = location
            
            print(f"⚠️  Following 308 redirect to: {redirect_url}")
            try:
                redirect_response = await client.post(
                    redirect_url,
                    json={...},
                    timeout=10.0
                )
                check_response = redirect_response
            except Exception as e:
                print(f"⚠️  Redirect failed: {e}")
                needs_approval = True
                violations = [f"Action Blocker Service redirect failed: {str(e)}"]
                # Continue to error handling below
    
    if check_response.status_code == 200:
        ...
    elif check_response.status_code == 503:
        ...
    else:
        violations = [f"Action Blocker Service error: {check_response.status_code}"]
```

### Location 2: Approve transaction endpoint (around line 690-713)

Apply the same fix pattern.

### Location 3: Status check endpoints (around line 867, 943)

For GET requests, add similar 308 handling.

## Alternative: Better URL Construction

Ensure URLs are always properly formatted:

```python
# Better URL construction
action_blocker_url_clean = action_blocker_url.rstrip('/')
endpoint = "/api/check-transaction"
if not endpoint.startswith('/'):
    endpoint = '/' + endpoint
full_url = f"{action_blocker_url_clean}{endpoint}"

# Ensure no double slashes
full_url = full_url.replace('//', '/').replace(':/', '://')
```

## Quick Test

After applying the fix, test with:
```bash
cd action-blocker
python test_exact_wallet_back.py
```

This should show if 308 redirects are being handled correctly.

