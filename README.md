# Upwork_discord_bot

## Current Fetch Architecture

- `src/upwork/job_search_client.py`
  - Primary GraphQL fetch flow.
  - Uses `cloudscraper` first.
  - On Cloudflare challenge (403), runs a one-time SeleniumBase cookie refresh and retries once.
  - Keeps auth stable and avoids rotating tokens on every run.

- `src/upwork/capture_loader.py`
  - Loads `cookies`, `headers`, `params`, and `json_data` from `data/cookies.py`.

- `src/auth/seleniumbase_session.py`
  - Browser-based cookie refresh helper used only for 403 recovery.

- `module2_fetch_once.py`
  - Thin runner that calls the project client and prints formatted jobs.

## Run

```powershell
d:/Learning_automation/Discord_Automation_Bot/.venv/Scripts/python.exe -u module2_fetch_once.py
```
