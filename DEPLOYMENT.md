# Deployment Runbook — ask.7mountainsmedia.com

Production stack: Plesk (AlmaLinux) → Node.js app (`server.js`) on the public
port → serves `chat-app/build` and proxies API routes → spawns Flask
(`chat_api.py`) on the backend port.

## Routine update (code changes only)

```bash
cd /path/to/rag-system
git pull
source venv/bin/activate
pip install -r requirements-production.txt          # only if requirements changed
cd chat-app && npm install && npm run build && cd .. # only if chat-app/ changed
```
Then restart the Node.js app in Plesk (Websites & Domains → Node.js → Restart App).

## Replacing the index (local digest → upload)

Index on a workstation to keep load off the server. Embeddings are billed the
same either way; the server just skips the hours of download/OCR/CPU work.

On the workstation:
```bash
# 1. Configure which folders to index (indexed_folders.json), then:
python incremental_indexer.py --sync

# 2. Package every configured folder
python collection_transfer.py export --all
```

On the server (clean slate — skip the `rm` line to merge instead of replace):
```bash
rm -rf chroma_db file_tracker.db indexed_folders.json
# upload the .ragpack.gz files into rag-system/, then:
venv/bin/python collection_transfer.py import folder_*.ragpack.gz
```
Restart the Node.js app. The import recreates `indexed_folders.json`, loads all
chunks without re-embedding, and seeds the file tracker so scheduled syncs are
incremental from the first run.

## Scheduled sync (every N days)

`.env` on the server:
```
SYNC_TIME=00:00           # UTC, HH:MM
SYNC_INTERVAL_DAYS=3      # sync every 3rd day
```

Plesk Scheduled Task, **daily**:
```bash
cd /path/to/rag-system && venv/bin/python scheduler.py --once
```
Runs that fall inside the interval exit immediately ("skipped"), so a daily
cron yields an every-N-days schedule. `--force` overrides. Only documents
whose *content* changed are re-embedded; renames and re-saves are detected
via content hash and cost nothing.

Manual sync: admin dashboard → Incremental Sync panel → "Sync Now"
(or "Dry Run" to preview).

## Required environment (server `.env`)

| Variable | Purpose |
|---|---|
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | User OAuth login |
| `JWT_SECRET_KEY` | Token signing — app warns loudly if missing |
| `FLASK_SECRET_KEY` | Session signing |
| `ALLOWED_DOMAINS` | e.g. `7mountainsmedia.com` |
| `ADMIN_EMAILS` | Comma-separated admin list (falls back to built-in) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account for Vertex AI |
| `GOOGLE_API_KEY` | Consumer Gemini API key (main agent path) |
| `CORS_ORIGINS` | `https://ask.7mountainsmedia.com` |
| `FLASK_ENV` | `production` |
| `SYNC_TIME`, `SYNC_INTERVAL_DAYS` | Scheduled sync (above) |

Never commit: `.env`, `credentials.json`, `token.pickle`,
`service-account-key.json`, `chroma_db/`, `file_tracker.db`,
`indexed_folders.json` — all gitignored.

## Model lifecycle

`GEMINI_MODEL` in `config.py`. **`gemini-2.5-flash` retires 2026-10-16** —
switch to a stable successor before then (candidates: `gemini-3.1-flash-lite`
for cost, `gemini-3.5-flash` for quality). Never use `-preview` model IDs in
production; the 09-2025 preview's retirement took the site down.

## Smoke test after deploy

1. `curl https://ask.7mountainsmedia.com/api/health` → healthy
2. Log in, confirm the collection picker lists the expected folders
3. Ask a question → answer cites sources with Drive links
4. Ask a follow-up ("tell me more") → conversation memory works
5. `/admin/dashboard` → stats load, Incremental Sync panel shows tracked files
