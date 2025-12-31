"""
Test ALL endpoints that wallet-back might call
to find which one is causing the 308 error
"""
import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_endpoint(url_base: str, endpoint: str, method: str = "GET", data: dict = None):
    """Test a specific endpoint"""
    url_clean = url_base.rstrip('/')
    full_url = f"{url_clean}{endpoint}"
    
    print(f"\n{'='*70}")
    print(f"Testing: {method} {full_url}")
    print(f"{'='*70}")
    
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as client:
            if method == "GET":
                response = await client.get(full_url)
            elif method == "POST":
                response = await client.post(full_url, json=data)
            else:
                print(f"[ERROR] Unsupported method: {method}")
                return
            
            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")
            
            if response.status_code == 308:
                print(f"\n[FOUND 308!] Permanent Redirect")
                print(f"Location: {response.headers.get('Location', 'N/A')}")
                print(f"Response: {response.text[:200]}")
                
                # Try following the redirect
                location = response.headers.get('Location')
                if location:
                    if location.startswith('/'):
                        redirect_url = f"{url_clean}{location}"
                    elif location.startswith('http'):
                        redirect_url = location
                    else:
                        redirect_url = f"{url_clean}/{location}"
                    
                    print(f"\nFollowing redirect to: {redirect_url}")
                    try:
                        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as redirect_client:
                            if method == "GET":
                                redirect_response = await redirect_client.get(redirect_url)
                            else:
                                redirect_response = await redirect_client.post(redirect_url, json=data)
                            
                            print(f"Redirect Status: {redirect_response.status_code}")
                            if redirect_response.status_code == 200:
                                try:
                                    print(f"Redirect Response: {json.dumps(redirect_response.json(), indent=2)}")
                                except:
                                    print(f"Redirect Response: {redirect_response.text[:200]}")
                    except Exception as e:
                        print(f"Redirect failed: {e}")
            elif response.status_code == 200:
                print(f"[SUCCESS] Request successful")
                try:
                    print(f"Response: {json.dumps(response.json(), indent=2)}")
                except:
                    print(f"Response: {response.text[:200]}")
            else:
                print(f"[ERROR] Status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 308:
            print(f"\n[FOUND 308!] (via exception)")
            print(f"Location: {e.response.headers.get('Location', 'N/A')}")
        else:
            print(f"\n[ERROR] HTTP {e.response.status_code}")
            print(f"Response: {e.response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")

async def test_all_wallet_back_endpoints():
    """Test all endpoints that wallet-back calls"""
    
    action_blocker_url = os.getenv("ACTION_BLOCKER_URL", "https://action-blocker.vercel.app")
    url_clean = action_blocker_url.rstrip('/')
    
    print("="*70)
    print("TESTING ALL WALLET-BACK ENDPOINTS")
    print("="*70)
    print(f"Base URL: {action_blocker_url}")
    print(f"Cleaned URL: {url_clean}")
    
    # Test all endpoints that wallet-back might call
    endpoints_to_test = [
        # Status endpoint (used in admin dashboard)
        ("/api/status", "GET", None),
        
        # Check transaction endpoint (used in transfer)
        ("/api/check-transaction", "POST", {
            "from_user_id": "test-user-1",
            "to_user_id": "test-user-2",
            "amount": 100.0,
            "sender_balance": 500.0
        }),
        
        # Root endpoint
        ("/", "GET", None),
        
        # Health endpoint
        ("/health", "GET", None),
    ]
    
    # Also test with trailing slash variations
    url_variations = [
        action_blocker_url,
        action_blocker_url.rstrip('/'),
        f"{action_blocker_url}/",
    ]
    
    for url_var in url_variations:
        print(f"\n\n{'#'*70}")
        print(f"Testing with URL: '{url_var}'")
        print(f"{'#'*70}")
        
        for endpoint, method, data in endpoints_to_test:
            await test_endpoint(url_var, endpoint, method, data)
            await asyncio.sleep(0.5)  # Small delay between requests

if __name__ == "__main__":
    asyncio.run(test_all_wallet_back_endpoints())

