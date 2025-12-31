"""
Test script that exactly replicates wallet-back's HTTP request
to reproduce the 308 error
"""
import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_exact_wallet_back_request():
    """Replicate the exact request wallet-back makes"""
    
    # Get the URL exactly as wallet-back does
    action_blocker_url = os.getenv("ACTION_BLOCKER_URL", "https://action-blocker.vercel.app")
    
    print("="*70)
    print("EXACT WALLET-BACK REQUEST SIMULATION")
    print("="*70)
    print(f"ACTION_BLOCKER_URL from env: '{action_blocker_url}'")
    
    # Exactly as in wallet-back/main.py line 327
    action_blocker_url_clean = action_blocker_url.rstrip('/')
    print(f"After rstrip('/'): '{action_blocker_url_clean}'")
    
    # Test data exactly as wallet-back sends
    test_data = {
        "from_user_id": "test-user-id-123",
        "to_user_id": "test-recipient-id-456",
        "amount": 100.0,
        "sender_balance": 500.0
    }
    
    # Construct URL exactly as wallet-back does (line 330)
    full_url = f"{action_blocker_url_clean}/api/check-transaction"
    print(f"Full URL: '{full_url}'")
    print("="*70)
    
    # Test with follow_redirects=True (as wallet-back does)
    print("\n[TEST 1] With follow_redirects=True (as wallet-back does)")
    print("-"*70)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.post(
                full_url,
                json=test_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            print(f"Status: {response.status_code}")
            print(f"Final URL: {response.url}")
            print(f"Request History: {len(response.history)} redirects")
            
            if response.history:
                print("\nRedirect History:")
                for i, hist_response in enumerate(response.history):
                    print(f"  {i+1}. {hist_response.status_code} -> {hist_response.headers.get('Location', 'N/A')}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n[SUCCESS] Response: {json.dumps(data, indent=2)}")
            else:
                print(f"\n[ERROR] Status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except httpx.TooManyRedirects as e:
        print(f"\n[ERROR] Too many redirects!")
        print(f"Request URL: {e.request.url}")
        if hasattr(e, 'response') and e.response:
            print(f"Response Status: {e.response.status_code}")
            print(f"Location: {e.response.headers.get('Location', 'N/A')}")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test with follow_redirects=False to see the 308
    print("\n\n[TEST 2] With follow_redirects=False (to see redirect)")
    print("-"*70)
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as client:
            response = await client.post(
                full_url,
                json=test_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")
            
            if response.status_code == 308:
                print(f"\n[FOUND] 308 Redirect!")
                print(f"Location: {response.headers.get('Location', 'N/A')}")
                print(f"Response: {response.text[:500]}")
                
                # Try the redirect location
                location = response.headers.get('Location')
                if location:
                    if location.startswith('/'):
                        redirect_url = f"{action_blocker_url_clean}{location}"
                    else:
                        redirect_url = location
                    print(f"\nTrying redirect URL: {redirect_url}")
                    
                    try:
                        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as redirect_client:
                            redirect_response = await redirect_client.post(
                                redirect_url,
                                json=test_data,
                                headers={
                                    "Content-Type": "application/json",
                                    "Accept": "application/json"
                                }
                            )
                            print(f"Redirect Status: {redirect_response.status_code}")
                            if redirect_response.status_code == 200:
                                print(f"Redirect Response: {json.dumps(redirect_response.json(), indent=2)}")
                    except Exception as e:
                        print(f"Redirect failed: {e}")
            elif response.status_code == 200:
                print(f"\n[SUCCESS] Direct 200 OK")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"\n[ERROR] Status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 308:
            print(f"\n[FOUND] 308 Redirect (via exception)!")
            print(f"Location: {e.response.headers.get('Location', 'N/A')}")
        else:
            print(f"\n[ERROR] HTTP {e.response.status_code}")
            print(f"Response: {e.response.text[:500]}")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    
    # Test different URL variations that might cause 308
    print("\n\n[TEST 3] Testing URL variations")
    print("-"*70)
    
    url_variations = [
        f"{action_blocker_url_clean}/api/check-transaction",
        f"{action_blocker_url_clean}/api/check-transaction/",
        f"{action_blocker_url}/api/check-transaction",
        f"{action_blocker_url}/api/check-transaction/",
    ]
    
    for test_url in url_variations:
        print(f"\nTesting: {test_url}")
        try:
            async with httpx.AsyncClient(follow_redirects=False, timeout=5.0) as client:
                response = await client.post(test_url, json=test_data)
                print(f"  Status: {response.status_code}", end="")
                if response.status_code == 308:
                    print(f" -> Location: {response.headers.get('Location', 'N/A')}")
                else:
                    print()
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_exact_wallet_back_request())

