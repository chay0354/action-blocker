"""
Comprehensive diagnostic script for 308 errors
Tests various scenarios to identify the exact problem
"""
import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Test URLs - try different variations
TEST_URLS = [
    "https://action-blocker.vercel.app",
    "https://action-blocker.vercel.app/",
    os.getenv("ACTION_BLOCKER_URL", "https://action-blocker.vercel.app"),
]

async def test_with_redirects(url_base: str, follow_redirects: bool):
    """Test with or without following redirects"""
    print(f"\n{'='*70}")
    print(f"Testing: {url_base}")
    print(f"Follow Redirects: {follow_redirects}")
    print(f"{'='*70}")
    
    # Clean URL
    url_clean = url_base.rstrip('/')
    endpoint = "/api/check-transaction"
    full_url = f"{url_clean}{endpoint}"
    
    test_data = {
        "from_user_id": "test-user-1",
        "to_user_id": "test-user-2",
        "amount": 100.0,
        "sender_balance": 500.0
    }
    
    print(f"Full URL: {full_url}")
    
    try:
        async with httpx.AsyncClient(follow_redirects=follow_redirects, timeout=10.0) as client:
            response = await client.post(full_url, json=test_data)
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response URL: {response.url}")
            print(f"Request URL: {response.request.url}")
            
            # Check for redirect headers
            if 'Location' in response.headers:
                print(f"Location Header: {response.headers['Location']}")
            
            # Print all headers
            print(f"\nResponse Headers:")
            for key, value in response.headers.items():
                if key.lower() in ['location', 'content-type', 'server', 'x-vercel-id']:
                    print(f"  {key}: {value}")
            
            if response.status_code == 200:
                print(f"\n[SUCCESS] Request successful!")
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"Response: {response.text[:200]}")
            elif response.status_code == 308:
                print(f"\n[ERROR] 308 Permanent Redirect detected!")
                print(f"Location: {response.headers.get('Location', 'Not set')}")
                print(f"Response text: {response.text[:500]}")
                
                # Try to follow the redirect manually
                if 'Location' in response.headers:
                    redirect_url = response.headers['Location']
                    if redirect_url.startswith('/'):
                        redirect_url = f"{url_clean}{redirect_url}"
                    print(f"\nTrying redirect URL: {redirect_url}")
                    try:
                        redirect_response = await client.post(redirect_url, json=test_data)
                        print(f"Redirect Status: {redirect_response.status_code}")
                        if redirect_response.status_code == 200:
                            print(f"Redirect Response: {json.dumps(redirect_response.json(), indent=2)}")
                    except Exception as e:
                        print(f"Redirect failed: {e}")
            else:
                print(f"\n[ERROR] Status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except httpx.TooManyRedirects as e:
        print(f"\n[ERROR] Too many redirects!")
        print(f"Request URL: {e.request.url}")
        print(f"Response URL: {e.response.url if hasattr(e, 'response') else 'N/A'}")
    except httpx.HTTPStatusError as e:
        print(f"\n[ERROR] HTTP {e.response.status_code}")
        print(f"Request URL: {e.request.url}")
        print(f"Response: {e.response.text[:500]}")
        if 'Location' in e.response.headers:
            print(f"Location: {e.response.headers['Location']}")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_all_scenarios():
    """Test all URL scenarios"""
    print("="*70)
    print("308 ERROR DIAGNOSTIC TEST")
    print("="*70)
    
    for url in TEST_URLS:
        if not url:
            continue
        
        # Test without following redirects first (to see the 308)
        await test_with_redirects(url, follow_redirects=False)
        
        # Test with following redirects (to see if it resolves)
        await test_with_redirects(url, follow_redirects=True)
        
        print("\n" + "="*70 + "\n")

async def test_url_construction():
    """Test how URLs are constructed"""
    print("\n" + "="*70)
    print("URL CONSTRUCTION TEST")
    print("="*70)
    
    base_urls = [
        "https://action-blocker.vercel.app",
        "https://action-blocker.vercel.app/",
        "https://action-blocker.vercel.app//",
    ]
    
    for base in base_urls:
        cleaned = base.rstrip('/')
        endpoint = "/api/check-transaction"
        full = f"{cleaned}{endpoint}"
        
        print(f"\nBase URL: '{base}'")
        print(f"After rstrip('/'): '{cleaned}'")
        print(f"Full URL: '{full}'")
        print(f"Has double slash: {'//' in full}")

if __name__ == "__main__":
    asyncio.run(test_url_construction())
    asyncio.run(test_all_scenarios())

