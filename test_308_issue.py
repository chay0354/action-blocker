"""
Test script specifically for 308 redirect issues
Tests different URL formats that might cause 308 errors
"""
import httpx
import json

# Test the main production URL with different formats
BASE_URL = "https://action-blocker.vercel.app"

def test_url_variations():
    """Test different URL formats that might cause 308 redirects"""
    
    test_data = {
        "from_user_id": "test-user-1",
        "to_user_id": "test-user-2",
        "amount": 100.0,
        "sender_balance": 500.0
    }
    
    # Test different URL formats
    url_variations = [
        f"{BASE_URL}/api/check-transaction",      # Normal
        f"{BASE_URL}/api/check-transaction/",     # With trailing slash
        f"{BASE_URL}/api/check-transaction//",   # Double slash
        f"{BASE_URL}/api/check-transaction ",    # With space (should fail)
    ]
    
    print("Testing URL variations for 308 redirects")
    print("="*60)
    
    for url in url_variations:
        print(f"\nTesting: POST {url}")
        print("-"*60)
        
        try:
            with httpx.Client(follow_redirects=False, timeout=10.0) as client:
                response = client.post(url, json=test_data)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 308:
                    print(f"[ERROR] 308 Permanent Redirect detected!")
                    print(f"Location: {response.headers.get('Location', 'Not set')}")
                    print(f"Response: {response.text[:200]}")
                elif response.status_code == 200:
                    print(f"[SUCCESS] Request successful")
                    try:
                        data = response.json()
                        print(f"Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"Response: {response.text[:200]}")
                else:
                    print(f"Response: {response.text[:200]}")
                    
        except httpx.TooManyRedirects:
            print(f"[ERROR] Too many redirects")
        except httpx.HTTPStatusError as e:
            print(f"[ERROR] HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_url_variations()

