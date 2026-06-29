# Main Experiment

oTree experiment with two rooms — **market** and **prescreen** — deployed on Heroku
with a Postgres database. This README covers the environment variables you need to
set, how to wire up the Heroku git remote and database, and how to configure the
session rooms.

---

## Initial setup (local)

Use **Python 3.10 or greater** — this is required for Heroku compatibility. Check with
`python --version` (you may need `python3` / `python3.10` on some systems).

```bash
# Clone and enter the project (skip the clone if you already have it)
git clone <repo-url>
cd <local-checkout-directory>

# Create and activate a virtual environment
python -m venv venv
. venv/bin/activate           # Windows: venv\Scripts\activate

# Upgrade pip *inside* the venv, then install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the local development server
otree devserver
```

`otree devserver` serves the site at <http://localhost:8000>. Leave `OTREE_PRODUCTION`
**unset** locally so you keep full debug error pages (see section 1). Stop the server
with `Ctrl-C`, and leave the venv with `deactivate`.

> **Note on ordering:** activate the venv *before* `pip install --upgrade pip` —
> otherwise you upgrade your system pip instead of the venv's.

To deploy this checkout to Heroku later, also install the **Heroku CLI** and run
`heroku login` (used throughout sections 3–4).

---

## 1. Environment variables

These are read at startup, so set them **before** launching the server (locally) or
**before** the first request (on Heroku). Restart / redeploy after changing any of them.

| Variable | Purpose | Example |
|---|---|---|
| `SSE_NUM_PRACTICE_ROUNDS` | Number of practice (unpaid, throwaway) rounds | `3` | (optional - defaults to 3)
| `SSE_NUM_ROUNDS` | Number of main (recorded) rounds | `30` | (optional - defaults to 30)
| `OTREE_ADMIN_PASSWORD` | Password for the `/admin` interface | `change-me` |
| `OTREE_AUTH_LEVEL` | Locks down the site | `STUDY` |
| `OTREE_PRODUCTION` | Turns **off** debug mode | `1` |
| `OTREE_SECRET_KEY` | Django secret key (set to a long random string in prod) | `…` |
| `DATABASE_URL` | Postgres connection string (set automatically by Heroku) | *(auto)* |

### Practice vs. main rounds

`SSE_NUM_PRACTICE_ROUNDS` and `SSE_NUM_ROUNDS` are **custom** variables — they are not
built into oTree. Read them in `settings.py` and feed them into the session config so
the app code can use them:

```python
# settings.py
import os

SSE_NUM_PRACTICE_ROUNDS = int(os.environ.get('SSE_NUM_PRACTICE_ROUNDS', 2))
SSE_NUM_ROUNDS = int(os.environ.get('SSE_NUM_ROUNDS', 20))

SESSION_CONFIGS = [
    dict(
        name='market',
        display_name='Market',
        app_sequence=['market'],
        num_demo_participants=4,
        num_practice_rounds=SSE_NUM_PRACTICE_ROUNDS,
        num_main_rounds=SSE_NUM_ROUNDS,
    ),
]
```

Then in your app, compute total rounds from the config (e.g.
`Constants.num_rounds = practice + main`, or read `session.config['num_practice_rounds']`
inside `creating_session`).

### Admin password

```bash
OTREE_ADMIN_PASSWORD=<your-password>
```

The admin username is `admin`. Set this to a strong value in production — anyone
with it can view and export participant data.

### Auth level

```bash
OTREE_AUTH_LEVEL=STUDY
```

- **`STUDY`** — recommended for live data collection. The whole site (including the
  demo page) requires the admin login; participants can only reach the game through a
  room link or session start link.
- **`DEMO`** — leaves the demo page open but password-protects the admin/data pages.
- **unset** — no auth at all. Never use this in production.

### Turn off debug

```bash
OTREE_PRODUCTION=1
```

Setting `OTREE_PRODUCTION=1` disables Django debug mode (no tracebacks shown to
participants, static files served correctly, etc.). Leave it **unset** while
developing locally so you get full error pages.

---

## 2. Where to set environment variables

**Locally** — export them in your shell, or put them in a `.env` file (do **not**
commit `.env`):

```bash
export OTREE_ADMIN_PASSWORD=change-me
export OTREE_AUTH_LEVEL=STUDY
export SSE_NUM_PRACTICE_ROUNDS=2
export SSE_NUM_ROUNDS=20
```

**On Heroku** — these are called *config vars*. Set them either from the CLI:

```bash
heroku config:set OTREE_ADMIN_PASSWORD=change-me -a <app-name>
heroku config:set OTREE_AUTH_LEVEL=STUDY -a <app-name>
heroku config:set OTREE_PRODUCTION=1 -a <app-name>
heroku config:set SSE_NUM_PRACTICE_ROUNDS=2 SSE_NUM_ROUNDS=20 -a <app-name>
```

…or in the Heroku Dashboard under **Settings → Config Vars → Reveal Config Vars**.
Config vars set here are injected as environment variables on every dyno and survive
restarts. Changing one triggers a restart automatically.

Confirm what is currently set with:

```bash
heroku config -a <app-name>
```

---

## 3. Set up the Heroku git remote

Create the app (or attach to an existing one) so that `git push heroku` deploys it.

**New app:**

```bash
heroku create <app-name>
# `heroku create` adds a remote named `heroku` automatically
```

**Existing app** — add the remote manually:

```bash
heroku git:remote -a <app-name>
```

Verify the remote is wired up:

```bash
git remote -v
# heroku  https://git.heroku.com/<app-name>.git (fetch)
# heroku  https://git.heroku.com/<app-name>.git (push)
```

Deploy by pushing your main branch:

```bash
git push heroku main
```

---

## 4. Set up Postgres on Heroku

oTree needs a real database in production (SQLite is not used on Heroku). Attach the
Postgres add-on — Heroku sets `DATABASE_URL` for you, which oTree reads automatically.

```bash
# Provision the database (entry-level paid plan)
heroku addons:create heroku-postgresql:essential-0 -a <app-name>

# Confirm DATABASE_URL was created
heroku config:get DATABASE_URL -a <app-name>
```

After the first deploy, run the oTree migrations / database reset:

```bash
heroku run "otree resetdb" -a <app-name>
```

> ⚠️ `resetdb` **wipes all data**. Only run it on first setup or when you intend to
> clear the database between studies. Export participant data first if you need it.

---

## 5. Rooms

Rooms give you persistent, reusable participant links. Define both rooms in
`settings.py`:

```python
# settings.py
ROOMS = [
    dict(
        name='market',
        display_name='Market',
        # participant_label_file='_rooms/market.txt',  # optional
    ),
    dict(
        name='prescreen',
        display_name='Prescreen',
    ),
]
```

Open the rooms from **Admin → Rooms**. Each room gives you a link to share with
participants and a live monitor of who is waiting / active.

### `market`

The main experiment room. Open it, create a `market` session, and share the room's
participant link. Round counts come from `SSE_NUM_PRACTICE_ROUNDS` / `SSE_NUM_ROUNDS`
(section 1).

### `prescreen`

The scheduling / availability room. Its key config item is a **session config field**,
**not** an environment variable. When you select the `prescreen` room and create its
session, oTree shows a configuration page with an editable text box:

> **Available times (space-separated):** `YYYYMMDD24mm`

You (the experimenter) type the time slots directly into that box at session-creation
time — no Heroku config var or redeploy is involved. Each slot is a single token in the
format `YYYYMMDD` + 24-hour hour + minutes (`YYYYMMDDHHmm`, 12 digits), and slots are
separated by spaces. For example, `202607011430` is **1 Jul 2026, 14:30**, so the box
might contain:

```
202607011430 202607011500 202607021000
```

To make that text box appear, define the field as an **editable** session config in
`settings.py`. Give it a default value (an empty string is fine) so oTree renders it as
an editable field on the session config page:

```python
# settings.py
SESSION_CONFIGS = [
    dict(
        name='prescreen',
        display_name='Prescreen',
        app_sequence=['prescreen'],
        num_demo_participants=1,
        # Editable text box shown when configuring the prescreen session.
        # Format per slot: YYYYMMDDHHmm (24-hour), space-separated.
        available_times='',
    ),
]
```

Inside the prescreen app, read whatever the experimenter typed and split it into the
list of slots:

```python
slots = session.config['available_times'].split()
```

`.split()` on whitespace turns the space-separated text into the list of slots your
prescreen app uses. (If `available_times` does **not** show up as editable on the
config page in your oTree version, add its name to `SESSION_FIELDS` / the session's
editable-fields list so it renders as a text box.)

---

## 6. Monitor and configure with the oTree launcher

Use the **oTree launcher** (the desktop/Hub tooling on
[otree.org](https://www.otree.org)) to monitor and configure your deployment without
working purely from the CLI. From it you can manage the Heroku app, view/set config
vars, watch the live session and room monitors, and pull data exports. It complements
the in-app Admin interface (`https://<app-name>.herokuapp.com/admin`) — see the
oTree documentation for installation and the current feature set, since the launcher
is updated independently of this experiment.

---

## Quick start checklist

1. `heroku create <app-name>` (or `heroku git:remote -a <app-name>`)
2. `heroku addons:create heroku-postgresql:essential-0 -a <app-name>`
3. `heroku config:set OTREE_ADMIN_PASSWORD=… OTREE_AUTH_LEVEL=STUDY OTREE_PRODUCTION=1 -a <app-name>`
4. `heroku config:set SSE_NUM_PRACTICE_ROUNDS=X  SSE_NUM_ROUNDS=XX -a <app-name>` (optional - defaults to 3 and 30 respectively)
5. `git push heroku main`
6. `heroku run "otree resetdb" -a <app-name>`
7. Open **Admin → Rooms** and launch the `market` and `prescreen` rooms.
8. When creating the `prescreen` session, enter the slots in the **Available times**
   text box on its config page (e.g. `202607011430 202607011500`).
