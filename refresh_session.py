#!/usr/bin/env python3
"""
Refresh Upwork session using SeleniumBase with localStorage/sessionStorage extraction.
Uses improved auth approach from auth_manager.py pattern.
"""
import json
from pathlib import Path
from src.auth.seleniumbase_session import refresh_cookies_with_seleniumbase

OUTPUT_FILE = Path("data/cookies.py")


def refresh_session():
    """Launch browser, extract tokens from localStorage + sessionStorage, save to cookies.py"""
    print("=== Refreshing Upwork Session (with localStorage/sessionStorage) ===")
    print(f"Output: {OUTPUT_FILE}")
    
    # Use improved function that extracts from all sources
    result = refresh_cookies_with_seleniumbase("https://www.upwork.com/nx/search/jobs/?q=python")
    
    if not result or not result.get("token"):
        print("ERROR: No token found after capture attempt.")
        return False
    
    print(f"\n✓ Token found: {result['token'][:50]}...")
    
    # Build cookies dict
    cookies_dict = {}
    for key, value in result.items():
        if key not in ("token", "cookies"):
            cookies_dict[key] = value
    
    print(f"✓ Total items captured: {len(cookies_dict)}")
    if cookies_dict:
        print(f"  Sample keys: {list(cookies_dict.keys())[:5]}")
    
    # Generate minimal headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    # Build GraphQL payload with correct query
    graphql_payload = {
        "query": """
  query VisitorJobSearch($requestVariables: VisitorJobSearchV1Request!) {
    search {
      universalSearchNuxt {
        visitorJobSearchV1(request: $requestVariables) {
          paging {
            total
            offset
            count
          }
          results {
            id
            title
            jobTile {
              job {
                id
                ciphertext: cipherText
                jobType
                weeklyRetainerBudget
                hourlyBudgetMin
                hourlyBudgetMax
                fixedPriceAmount {
                  isoCurrencyCode
                  amount
                }
              }
            }
          }
        }
      }
    }
  }
        """,
        "variables": {
            "requestVariables": {
                "userQuery": "web development",
                "paging": {
                    "offset": 0,
                    "count": 10
                }
            }
        }
    }
    
    # Add bearer token to headers
    if result.get("token"):
        headers["Authorization"] = f"Bearer {result['token']}"
    
    print("\n[5] Saving to data/cookies.py...")
    payload_json = json.dumps(graphql_payload, indent=2)
    
    output_content = f'''"""
Auto-captured Upwork session (refreshed via SeleniumBase localStorage extraction)
DO NOT EDIT - regenerate with: python refresh_session.py
Bearer token extracted from: window.localStorage or window.sessionStorage
"""

cookies = {json.dumps(cookies_dict, indent=4)}

headers = {json.dumps(headers, indent=4)}

params = {{}}

json_data = {payload_json}
'''
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(output_content)
    
    print(f"✓ Session saved to {OUTPUT_FILE}")
    print(f"✓ {len(cookies_dict)} cookies/storage items captured")
    print(f"✓ Bearer token: {result['token'][:40]}...")
    return True


if __name__ == "__main__":
    try:
        success = refresh_session()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
