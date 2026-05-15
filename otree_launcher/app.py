"""
oTree Session Creator - Flask backend
Proxies REST calls to oTree and manages config persistence.
"""

import csv
import hashlib
import io
import json
import requests
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

CONFIG_FILE = Path.home() / ".otree_session_creator.json"

def compute_export_hash(secret_key: str, admin_password: str = '') -> str:
    """
    Replicates oTree's DATA_EXPORT_HASH computation from otree/common.py:
        _SECRET = settings.SECRET_KEY + (settings.ADMIN_PASSWORD or '')
        make_hash(s) -> sha224(s + _SECRET)[:8]
        DATA_EXPORT_HASH = make_hash('dataexport')
    """
    _secret = secret_key + (admin_password or '')
    s = 'dataexport' + _secret
    return hashlib.sha224(s.encode()).hexdigest()[:8]

# In-memory set of participant codes we have dropped this run.
dropped_codes: set = set()

DEFAULT_CONFIG = {
    # ── Connection ──────────────────────────────────────────────
    "serverMode": "remote",
    "remoteUrl":  "https://vt-market-experiment.herokuapp.com",
    "localUrl":   "http://localhost:8000",
    "restKey":    "s+Uj_g5Zunap3?TfZ6uUQ7",
    "secretKey":  "7763949237284",   # settings.py SECRET_KEY
    "adminPassword": "",             # OTREE_ADMIN_PASSWORD env var (blank for devserver)

    # ── Session ─────────────────────────────────────────────────
    "sessionConfigName": "whole_exp",
    "roomName":          "CTlanding",
    "numSubjects":       25,

    # ── Core params ─────────────────────────────────────────────
    "participationFee": 12.00,
    "rwcpp":            0.005,
    "showNext":         False,
    "endowStock":       "4 4 4",

    # Prescreening-only
    "screenFee":   0.50,
    "screenTimes": "",

    # Prolific completion URLs
    "compUrlExp": "https://app.prolific.com/submissions/complete?cc=CT8QWJ3A",
    "compUrlPre": "https://app.prolific.com/submissions/complete?cc=C1BNU59M",

    # ── Landing / consent (whole_exp) ───────────────────────────
    "instructionId":      "232inD_HChc",
    "waitingGroupSize":   25,
    "landingWaitTimeout": 1200,

    # ── Advanced: market timing (seconds) ───────────────────────
    "marketTime":       20,
    "fixateTime":       2,
    "forecastTime":     30,
    "summaryTime":      10,
    "practiceTime":     15,
    "practiceEndTime":  30,
    "finalResultsTime": 75,
    "riskElicTime":     5,

    # ── Advanced: dividends & market ────────────────────────────
    "interestRate":  0.05,
    "initialPrice":  14.0,
    "divAmount":     "0.40 1.00",
    "divDist":       ".5 .5",
    "endowWorth":    156.0,
    "floatRatioCap": 1.0,

    # ── Advanced: margin ────────────────────────────────────────
    "marginRatio":       0.5,
    "marginPremium":     0.1,
    "marginTargetRatio": 0.6,
    "autoTransDelay":    0,

    # ── Advanced: forecasting ───────────────────────────────────
    "forecastThold":   2.5,
    "forecastReward":  2.5,
    "forecastRange":   50,
    "forecastPeriods": "0,2,5,10",

    # ── Advanced: rewards ───────────────────────────────────────
    "quizReward": 0.25,
    "bonusCap":   "",

    # ── Advanced: flags ─────────────────────────────────────────
    "isProlific": False,
    "isMturk":    False,
    "isPilot":    False,
    "randomHist": False,

    # ── Advanced: expected time ─────────────────────────────────
    "expectedTimePilot": 1,
    "expectedTimeLive":  2,
}


# ── Config endpoints ──────────────────────────────────────────────────────────

@app.route("/config", methods=["GET"])
def get_config():
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text())
            return jsonify({**DEFAULT_CONFIG, **saved})
        except Exception as e:
            return jsonify({**DEFAULT_CONFIG, "error": str(e)}), 200
    return jsonify(DEFAULT_CONFIG)


@app.route("/config", methods=["POST"])
def save_config():
    data = request.get_json()
    try:
        CONFIG_FILE.write_text(json.dumps(data, indent=2))
        return jsonify({"ok": True, "path": str(CONFIG_FILE)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/config/path", methods=["GET"])
def config_path():
    return jsonify({"path": str(CONFIG_FILE), "exists": CONFIG_FILE.exists()})


# ── oTree helpers ─────────────────────────────────────────────────────────────

def _headers(rest_key):
    h = {"Content-Type": "application/json"}
    if rest_key:
        h["otree-rest-key"] = rest_key
    return h


def _get_otree(path, base_url, rest_key, timeout=8):
    try:
        r = requests.get(
            f"{base_url}/api/{path}/",
            headers=_headers(rest_key),
            timeout=timeout,
        )
        if r.ok:
            return r.json(), None
        return None, f"HTTP {r.status_code}: {r.text[:200]}"
    except requests.exceptions.ConnectionError:
        return None, "Connection refused — is oTree running?"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except Exception as e:
        return None, str(e)


# ── Standard proxy endpoints ──────────────────────────────────────────────────

@app.route("/proxy/test", methods=["POST"])
def proxy_test():
    body = request.get_json()
    base_url = body.get("baseUrl", "").rstrip("/")
    rest_key = body.get("restKey", "")
    data, err = _get_otree("otree_version", base_url, rest_key)
    if err:
        return jsonify({"ok": False, "status": 0, "text": err})
    return jsonify({"ok": True, "status": 200, "text": json.dumps(data)})


@app.route("/proxy/session_configs", methods=["POST"])
def proxy_session_configs():
    body = request.get_json()
    base_url = body.get("baseUrl", "").rstrip("/")
    rest_key = body.get("restKey", "")
    data, err = _get_otree("session_configs", base_url, rest_key)
    if err:
        return jsonify({"ok": False, "text": err})
    configs = [{"name": c.get("name", ""), "doc": c.get("doc", "")} for c in data]
    return jsonify({"ok": True, "configs": configs})


@app.route("/proxy/rooms", methods=["POST"])
def proxy_rooms():
    body = request.get_json()
    base_url = body.get("baseUrl", "").rstrip("/")
    rest_key = body.get("restKey", "")
    data, err = _get_otree("rooms", base_url, rest_key)
    if err:
        return jsonify({"ok": False, "text": err})
    rooms = [{"name": r.get("name", ""), "display_name": r.get("display_name", r.get("name", ""))} for r in data]
    return jsonify({"ok": True, "rooms": rooms})


@app.route("/proxy/create_session", methods=["POST"])
def proxy_create_session():
    body = request.get_json()
    base_url = body.pop("baseUrl", "").rstrip("/")
    rest_key = body.pop("restKey", "")
    try:
        r = requests.post(
            f"{base_url}/api/sessions/",
            json=body,
            headers=_headers(rest_key),
            timeout=20,
        )
        if r.ok:
            return jsonify({"ok": True, "data": r.json()})
        return jsonify({"ok": False, "status": r.status_code, "text": r.text})
    except Exception as e:
        return jsonify({"ok": False, "status": 0, "text": str(e)})


@app.route("/proxy/set_vars", methods=["POST"])
def proxy_set_vars():
    body = request.get_json()
    base_url = body.pop("baseUrl", "").rstrip("/")
    rest_key = body.pop("restKey", "")
    session_code = body.pop("sessionCode", "")
    try:
        r = requests.post(
            f"{base_url}/api/session_vars/{session_code}/",
            json=body,
            headers=_headers(rest_key),
            timeout=10,
        )
        if r.ok:
            return jsonify({"ok": True})
        return jsonify({"ok": False, "status": r.status_code, "text": r.text})
    except Exception as e:
        return jsonify({"ok": False, "status": 0, "text": str(e)})


# ── Session data: REST API (basic 5 fields) ───────────────────────────────────

@app.route("/proxy/session_data", methods=["POST"])
def proxy_session_data():
    """
    Basic participant list via REST API — only 5 fields available.
    Used as fallback if export endpoint is unavailable.
    Augments with is_dropout from our in-memory dropped_codes set.
    """
    body = request.get_json()
    base_url     = body.get("baseUrl", "").rstrip("/")
    rest_key     = body.get("restKey", "")
    session_code = body.get("sessionCode", "")

    data, err = _get_otree(f"sessions/{session_code}", base_url, rest_key, timeout=10)
    if err:
        return jsonify({"ok": False, "text": err})

    participants = data.get("participants", [])
    rows = []
    for p in participants:
        code = p.get("code", "")
        rows.append({
            "code":          code,
            "label":         p.get("label") or "",
            "id_in_session": p.get("id_in_session", ""),
            "finished":      p.get("finished", False),
            "payoff":        p.get("payoff_in_real_world_currency", 0.0),
            "is_dropout":    code in dropped_codes,
            # these are empty in the basic REST response
            "current_app":   "",
            "current_page":  "",
            "round_number":  "",
        })
    rows.sort(key=lambda r: r["id_in_session"] or 0)
    return jsonify({"ok": True, "participants": rows, "source": "rest"})


# ── Session data: ExportSessionWide (rich fields) ─────────────────────────────

@app.route("/proxy/session_data_rich", methods=["POST"])
def proxy_session_data_rich():
    """
    Fetch participant status via ExportSessionWide CSV.
    The DATA_EXPORT_HASH token is deterministic:
        hashlib.sha224('dataexport'.encode()).hexdigest()[:8]
    This gives access to _current_app_name, _current_page_name,
    _round_number, and any PARTICIPANT_FIELDS you've defined.
    """
    body = request.get_json()
    base_url      = body.get("baseUrl", "").rstrip("/")
    session_code  = body.get("sessionCode", "")
    secret_key    = body.get("secretKey", "")
    admin_password= body.get("adminPassword", "")

    token = compute_export_hash(secret_key, admin_password)
    url = f"{base_url}/ExportSessionWide/{session_code}/"
    try:
        r = requests.get(url, params={"token": token}, timeout=15)
        if not r.ok:
            return jsonify({
                "ok": False,
                "text": f"HTTP {r.status_code}: {r.text[:200]}"
            })
    except requests.exceptions.ConnectionError:
        return jsonify({"ok": False, "text": "Connection refused — is oTree running?"})
    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "text": "Request timed out"})
    except Exception as e:
        return jsonify({"ok": False, "text": str(e)})

    # Parse the CSV. oTree exports with a UTF-8 BOM sometimes.
    text = r.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    # The wide export has one row per participant (per round for multi-round
    # apps it repeats — we only want the latest row per participant code).
    # Key fields from oTree's wide export:
    #   participant.code, participant.label, participant._current_app_name,
    #   participant._current_page_name, participant._round_number,
    #   participant.finished (if defined), participant.is_dropout (if defined)
    by_code = {}
    for row in reader:
        code = row.get("participant.code", "")
        if not code:
            continue
        # Keep the row with the highest round number (most recent state)
        existing = by_code.get(code)
        try:
            this_round = int(row.get("participant._round_number", 0) or 0)
        except ValueError:
            this_round = 0
        if existing is None or this_round >= existing.get("_round_int", 0):
            by_code[code] = {**row, "_round_int": this_round}

    rows = []
    for code, row in by_code.items():
        # Normalise finished/is_dropout which may be 'True'/'False' strings
        def to_bool(v):
            return str(v).strip().lower() in ('true', '1', 'yes')

        finished   = to_bool(row.get("participant.finished", False))
        is_dropout = code in dropped_codes or to_bool(
            row.get("participant.is_dropout", False)
        )
        try:
            id_in_session = int(row.get("participant.id_in_session", 0) or 0)
        except ValueError:
            id_in_session = 0
        try:
            payoff_pts = float(row.get("participant.payoff", 0) or 0)
            rwcpp      = float(row.get("session.config.real_world_currency_per_point", 0.005) or 0.005)
            payoff     = round(payoff_pts * rwcpp, 2)
        except (ValueError, TypeError):
            payoff = 0.0

        rows.append({
            "code":          code,
            "label":         row.get("participant.label") or "",
            "id_in_session": id_in_session,
            "current_app":   row.get("participant._current_app_name", "") or "",
            "current_page":  row.get("participant._current_page_name", "") or "",
            "round_number":  row.get("participant._round_number", "") or "",
            "finished":      finished,
            "is_dropout":    is_dropout,
            "payoff":        payoff,
        })

    rows.sort(key=lambda r: r["id_in_session"] or 0)
    return jsonify({"ok": True, "participants": rows, "source": "export"})


# ── Drop participant ──────────────────────────────────────────────────────────

@app.route("/proxy/drop_participant", methods=["POST"])
def proxy_drop_participant():
    body = request.get_json()
    base_url         = body.get("baseUrl", "").rstrip("/")
    rest_key         = body.get("restKey", "")
    participant_code = body.get("participantCode", "")
    try:
        r = requests.post(
            f"{base_url}/api/participant_vars/{participant_code}/",
            json={"vars": {"is_dropout": True}},
            headers=_headers(rest_key),
            timeout=10,
        )
        if r.ok:
            dropped_codes.add(participant_code)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "status": r.status_code, "text": r.text})
    except Exception as e:
        return jsonify({"ok": False, "status": 0, "text": str(e)})


# ── Serve frontend ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(port=5055, debug=False)
