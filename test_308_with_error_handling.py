"""
Test script that simulates wallet-back's error handling
to see when 308 errors are reported
"""
import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def simulate_wallet_back_error_handling():
    """Simulate exactly how wallet-back handles responses and errors"""
    
    action_blocker_url = os.getenv("ACTION_BLOCKER_URL", "https://action-blocker.vercel.app")
    action_blocker_url_clean = action_blocker_url.rstrip('/')
    
    test_data = {
        "from_user_id": "test-user-1",
        "to_user_id": "test-user-2",
        "amount": 100.0,
        "sender_balance": 500.0
    }
    
    print("="*70)
    print("SIMULATING WALLET-BACK ERROR HANDLING")
    print("="*70)
    print(f"URL: {action_blocker_url_clean}/api/check-transaction")
    
    # Simulate wallet-back's exact code flow
    needs_approval = False
    violations = []
    
    try:
        # This is exactly what wallet-back does (line 328-338)
        async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
            check_response = await client.post(
                f"{action_blocker_url_clean}/api/check-transaction",
                json=test_data
            )
            
            print(f"\nResponse Status: {check_response.status_code}")
            print(f"Response URL: {check_response.url}")
            print(f"Redirect History: {len(check_response.history)}")
            
            if check_response.history:
                print("\nRedirect History:")
                for i, hist in enumerate(check_response.history):
                    print(f"  {i+1}. {hist.status_code} {hist.url} -> {hist.headers.get('Location', 'N/A')}")
            
            # This is wallet-back's error handling (line 340-353)
            if check_response.status_code == 200:
                check_data = check_response.json()
                needs_approval = check_data.get("needs_approval", False)
                violations = check_data.get("violations", [])
                print(f"\n[SUCCESS] Transaction check passed")
                print(f"  Needs approval: {needs_approval}")
                print(f"  Violations: {violations}")
            elif check_response.status_code == 503:
                # Service not running - block transaction for safety
                needs_approval = True
                violations = ["Action Blocker Service is not running. Transaction blocked for safety."]
                print(f"\n[WARNING] Service not available - blocking transaction")
            else:
                # Error from service - block transaction for safety
                needs_approval = True
                violations = [f"Action Blocker Service error: {check_response.status_code}"]
                print(f"\n[ERROR] Action Blocker Service error: {check_response.status_code}")
                print(f"  Response: {check_response.text[:200]}")
                
    except httpx.TimeoutException:
        # Timeout - block transaction for safety
        needs_approval = True
        violations = ["Action Blocker Service timeout. Transaction blocked for safety."]
        print(f"\n[ERROR] Timeout - blocking transaction")
    except httpx.HTTPStatusError as e:
        # This might catch 308 if follow_redirects=False
        print(f"\n[ERROR] HTTPStatusError: {e.response.status_code}")
        print(f"  Request URL: {e.request.url}")
        print(f"  Response URL: {e.response.url}")
        if e.response.status_code == 308:
            print(f"  Location: {e.response.headers.get('Location', 'N/A')}")
        needs_approval = True
        violations = [f"Action Blocker Service error: {e.response.status_code}"]
    except Exception as e:
        # Any other error - block transaction for safety
        needs_approval = True
        violations = [f"Action Blocker Service error: {str(e)}"]
        print(f"\n[ERROR] Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"Final Result:")
    print(f"  Needs approval: {needs_approval}")
    print(f"  Violations: {violations}")
    print(f"{'='*70}")

async def test_with_different_scenarios():
    """Test different scenarios that might cause 308"""
    
    print("\n\n" + "="*70)
    print("TESTING DIFFERENT SCENARIOS")
    print("="*70)
    
    # Test 1: Normal request
    print("\n[SCENARIO 1] Normal request")
    await simulate_wallet_back_error_handling()
    
    # Test 2: With a URL that has trailing slash
    print("\n\n[SCENARIO 2] URL with trailing slash in env var")
    os.environ["ACTION_BLOCKER_URL"] = "https://action-blocker.vercel.app/"
    await simulate_wallet_back_error_handling()
    
    # Test 3: With a URL that might cause issues
    print("\n\n[SCENARIO 3] Testing with different URL format")
    test_urls = [
        "https://action-blocker.vercel.app",
        "https://action-blocker.vercel.app/",
    ]
    
    for test_url in test_urls:
        print(f"\n--- Testing with: {test_url} ---")
        os.environ["ACTION_BLOCKER_URL"] = test_url
        await simulate_wallet_back_error_handling()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_with_different_scenarios())









