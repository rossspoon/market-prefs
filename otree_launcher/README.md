# oTree Session Creator

A standalone desktop GUI for creating oTree sessions via the REST API.
Works with both local (`devserver`) and remote (Heroku) oTree servers.

## Setup (one-time)

1. Make sure Python 3.8+ is installed.

2. Install dependencies:
   ```
   pip install flask requests
   ```
   Or using the requirements file:
   ```
   pip install -r requirements.txt
   ```

## Running the app

Just double-click **`launcher.py`** — or from a terminal:
```
python launcher.py
```

The app opens automatically in your default browser at `http://localhost:5055`.
Close the terminal window (or press Ctrl-C) to stop it.

## Configuration file

Settings are saved to:
- **Mac/Linux:** `~/.otree_session_creator.json`
- **Windows:** `C:\Users\<you>\.otree_session_creator.json`

The path is shown in the top-right of the app window.

## oTree REST Key

### Remote server (Heroku)
Set the `OTREE_REST_KEY` config var on Heroku and paste the value into the
"REST Key" field. The key is passed as the `otree-rest-key` header on every
API request.

### Local devserver
When running `otree devserver` without `OTREE_AUTH_LEVEL` set, **no REST key
is needed** — leave the field blank. The devserver allows unauthenticated API
access by default.

If you *have* set `OTREE_AUTH_LEVEL=DEMO` or `STUDY` locally, you must also
set `OTREE_REST_KEY` in your environment before starting oTree:

**Mac/Linux:**
```bash
export OTREE_REST_KEY=your-secret-key
otree devserver
```

**Windows (Command Prompt):**
```
set OTREE_REST_KEY=your-secret-key
otree devserver
```

**Windows (PowerShell):**
```powershell
$env:OTREE_REST_KEY = "your-secret-key"
otree devserver
```

## File structure

```
otree_launcher/
├── launcher.py        ← double-click to run
├── app.py             ← Flask backend (proxy + config API)
├── requirements.txt
├── README.md
└── static/
    └── index.html     ← the full UI
```
