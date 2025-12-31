"""
Simulate exactly how wallet-back calls the action blocker
to reproduce the 308 error
"""
import os
import httpx
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

async def test_like_wallet_back():
    """Test exactly how wallet-back makes the call"""
    
    # Get URL from environment (like wallet-back does)
    action_blocker_url = os.getenv("ACTION_BLOCKER_URL", "https://action-blocker.vercel.app")
    
    print(f"ACTION_BLOCKER_URL from env: '{action_blocker_url}'")
    print("="*60)
    
    # Simulate wallet-back's exact code
    action_blocker_url_clean = action_blocker_url.rstrip('/')
    print(f"After rstrip('/'): '{action_blocker_url_clean}'")
    
    test_data = {
        "from_user_id": "test-user-1",
        "to_user_id": "test-user-2",
        "amount": 100.0,
        "sender_balance": 500.0
    }
    
    full_url = f"{action_blocker_url_clean}/api/check-transaction"
    print(f"Full URL: '{full_url}'")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            print(f"\nMaking POST request to: {full_url}")
            check_response = await client.post(
                full_url,
                json=test_data
            )
            
            print(f"\nStatus Code: {check_response.status_code}")
            print(f"Headers: {dict(check_response.headers)}")
            
            if check_response.status_code == 200:
                print("[SUCCESS] Request successful!")
                data = check_response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            elif check_response.status_code == 308:
                print("[ERROR] 308 Permanent Redirect!")
                print(f"Location: {check_response.headers.get('Location', 'Not set')}")
                print(f"Response: {check_response.text}")
            else:
                print(f"[ERROR] Status {check_response.status_code}")
                print(f"Response: {check_response.text}")
                
    except httpx.TooManyRedirects as e:
        print(f"[ERROR] Too many redirects: {e}")
        print(f"Final URL: {e.request.url}")
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] HTTP {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_like_wallet_back())

