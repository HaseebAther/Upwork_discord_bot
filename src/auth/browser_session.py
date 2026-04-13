"""Selenium-based browser automation for Upwork session management."""
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def extract_cookies_from_browser(
    upwork_url: str = "https://www.upwork.com/jobs/search",
    headless: bool = True,
    timeout: int = 30,
) -> dict[str, str]:
    """
    Open Chrome browser, navigate to Upwork, wait for page load, extract cookies.
    
    This ensures requests have legitimate browser session context, avoiding
    anti-bot detection that would block headless HTTP-only requests.
    
    Args:
        upwork_url: URL to navigate to (default: jobs search)
        headless: Run browser in headless mode (no GUI)
        timeout: Max seconds to wait for page load
        
    Returns:
        Dictionary of cookie name -> value
        
    Raises:
        TimeoutException: If page doesn't load within timeout
        Exception: If browser fails to start
    """
    print(f"Starting Chrome browser (headless={headless})...")
    
    options = Options()
    if headless:
        options.add_argument("--headless=new")  # New headless mode (more stable)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    )
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print(f"Navigating to {upwork_url}...")
        driver.get(upwork_url)
        
        # Wait for page to be interactive (look for job search results or main content)
        print(f"Waiting up to {timeout}s for page load...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
        )
        
        # Extra wait for dynamic content (React/Vue might still be loading)
        time.sleep(3)
        
        print("Page loaded. Extracting cookies...")
        
        # Get all cookies
        cookies_list = driver.get_cookies()
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies_list}
        
        print(f"Extracted {len(cookies_dict)} cookies from browser session")
        
        return cookies_dict
        
    finally:
        if driver:
            driver.quit()
            print("Browser closed")


def extract_headers_from_browser(
    upwork_url: str = "https://www.upwork.com/jobs/search",
) -> dict[str, str]:
    """
    Open Chrome, navigate to Upwork, intercept GraphQL request, extract headers.
    
    This is tricky with Selenium alone (no built-in request interception).
    For now, return a minimal set of common headers that work with Upwork.
    
    Full header extraction would require:
    - Selenium with Chrome DevTools Protocol (CDP)
    - Or Playwright (better request interception)
    - Or reverse-proxy like mitmproxy
    
    For this quickstart, we return headers that have worked in testing.
    """
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.upwork.com",
        "referer": upwork_url,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-upwork-accept-language": "en-US",
    }


def save_cookies_to_file(
    cookies: dict[str, str],
    file_path: Path = Path("data/cookies.py"),
) -> None:
    """
    Save cookies dict to data/cookies.py for use by module2_fetch_once.py.
    
    Preserves the existing structure (headers, params, json_data if present).
    """
    # Read existing file if it exists to preserve other data
    existing_data = {}
    if file_path.exists():
        try:
            content = file_path.read_text()
            # Parse existing dicts (simplified; assumes well-formed Python)
            import ast
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Name):
                        try:
                            existing_data[target.id] = ast.literal_eval(node.value)
                        except Exception:
                            pass
        except Exception as e:
            print(f"Warning: Could not parse existing cookies.py: {e}")
    
    # Update/add cookies
    existing_data["cookies"] = cookies
    
    # Build new file content
    lines = []
    for key in ["cookies", "headers", "params", "json_data"]:
        if key in existing_data:
            lines.append(f"{key} = {repr(existing_data[key])}\n")
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("".join(lines), encoding="utf-8")
    print(f"Saved cookies to {file_path}")


def refresh_browser_session(
    output_file: Path = Path("data/cookies.py"),
    upwork_url: str = "https://www.upwork.com/jobs/search",
) -> dict[str, str]:
    """
    Master function: Extract cookies from live browser, save to file, return them.
    
    This is meant to be called:
    1. On startup (to get initial session)
    2. Periodically (every 11 hours or on 401 errors)
    3. When auth fails, as a recovery mechanism
    """
    cookies = extract_cookies_from_browser(upwork_url=upwork_url, headless=True)
    save_cookies_to_file(cookies, output_file)
    return cookies


if __name__ == "__main__":
    # Quick test
    print("Testing browser session extraction...")
    cookies = refresh_browser_session()
    print(f"\nSuccessfully extracted {len(cookies)} cookies")
    print("Sample cookies (first 3):")
    for k, v in list(cookies.items())[:3]:
        print(f"  {k}: {v[:50]}...")
