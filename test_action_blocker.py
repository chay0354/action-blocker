"""
Test script to check Action Blocker Service API
Tests both local and Vercel deployments
"""
import os
import sys
import httpx
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test URLs - try both local and Vercel
TEST_URLS = [
    os.getenv("ACTION_BLOCKER_URL", "http://127.0.0.1:8001"),
    "https://action-blocker.vercel.app",
    "https://action-blocker-gsjf71098-chays-projects-636530ab.vercel.app"
]

def test_endpoint(url: str, endpoint: str, method: str = "GET", data: dict = None):
    """Test a specific endpoint"""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {full_url}")
    print(f"{'='*60}")
    
    try:
        with httpx.Client(follow_redirects=True, timeout=10.0) as client:
            if method == "GET":
                response = client.get(full_url)
            elif method == "POST":
                response = client.post(full_url, json=data)
            else:
                print(f"[ERROR] Unsupported method: {method}")
                return
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    print(f"Response: {json.dumps(response.json(), indent=2)}")
                except:
                    print(f"Response (text): {response.text}")
            elif response.status_code == 308:
                print(f"[ERROR] 308 Permanent Redirect!")
                print(f"Location header: {response.headers.get('Location', 'Not set')}")
                print(f"Response text: {response.text}")
            else:
                print(f"Response: {response.text}")
                
    except httpx.TimeoutException:
        print(f"[ERROR] Timeout - Service not responding")
    except httpx.ConnectError:
        print(f"[ERROR] Connection Error - Cannot connect to {url}")
    except Exception as e:
        print(f"[ERROR] Error: {type(e).__name__}: {str(e)}")

def test_transaction_check(url: str):
    """Test the transaction check endpoint"""
    test_data = {
        "from_user_id": "test-user-1",
        "to_user_id": "test-user-2",
        "amount": 100.0,
        "sender_balance": 500.0
    }
    
    print(f"\n{'#'*60}")
    print(f"Testing Transaction Check")
    print(f"{'#'*60}")
    test_endpoint(url, "/api/check-transaction", method="POST", data=test_data)

def main():
    print("Action Blocker Service Test Script")
    print("="*60)
    
    # Test each URL
    for url in TEST_URLS:
        if not url:
            continue
            
        print(f"\n\n{'#'*60}")
        print(f"Testing URL: {url}")
        print(f"{'#'*60}")
        
        # Test root endpoint
        test_endpoint(url, "/", method="GET")
        
        # Test health endpoint
        test_endpoint(url, "/health", method="GET")
        
        # Test status endpoint
        test_endpoint(url, "/api/status", method="GET")
        
        # Test transaction check
        test_transaction_check(url)
        
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()

