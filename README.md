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

- `module3_polling_loop.py`
  - Long-running polling loop.
  - Refreshes cookies on startup.
  - Reauths on 401/403 and keeps the loop alive until Ctrl+C.
  - Persists runtime state in `data/polling_state.json`.
  - Stores job history and poll run logs in `data/runtime.db`.
  - Posts new jobs to Discord via webhook when configured.

## Run

```powershell
d:/Learning_automation/Discord_Automation_Bot/.venv/Scripts/python.exe -u module2_fetch_once.py
```

```powershell
d:/Learning_automation/Discord_Automation_Bot/.venv/Scripts/python.exe -u app.py --query "python dev" --interval 180
```

With Discord posting enabled:

```powershell
$env:DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
d:/Learning_automation/Discord_Automation_Bot/.venv/Scripts/python.exe -u app.py --query "python dev" --interval 180 --discord-max-posts 5
```

Or pass webhook URL directly:

```powershell
d:/Learning_automation/Discord_Automation_Bot/.venv/Scripts/python.exe -u app.py --query "python dev" --interval 180 --discord-webhook-url "https://discord.com/api/webhooks/..." --discord-max-posts 5
```

Direct polling runner (same runtime, optional):

```powershell
d:/Learning_automation/Discord_Automation_Bot/.venv/Scripts/python.exe -u module3_polling_loop.py --query "python dev" --interval 180
```
