from flask import Flask, render_template, request, jsonify, send_file, Response
import threading
import time
import os
import glob
import io
from Main import GimkitBot, questions

app = Flask(__name__)

bot_status = {
    "running": False,
    "message": "Idle",
    "game_mode": "",
    "questions_learned": 0,
}
bot_instance = None
bot_thread   = None
_bot_lock    = threading.Lock()

# ── Screenshot cache ───────────────────────────────────────────────────────────
# A background thread continuously captures the browser and stores the JPEG here.
# /screenshot returns from this cache instantly — never blocks on ChromeDriver.
_cached_screen      = None
_cached_screen_lock = threading.Lock()


def _screenshot_worker(inst):
    """Background thread: capture browser every ~400 ms into an in-memory cache."""
    global _cached_screen
    from PIL import Image
    while True:
        # Stop if bot was reset/replaced
        with _bot_lock:
            if bot_instance is not inst:
                break
        try:
            png = inst.driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(png))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=72)
            data = buf.getvalue()
            with _cached_screen_lock:
                _cached_screen = data
        except Exception:
            pass
        time.sleep(0.4)

    # Clear cache when this bot exits
    with _cached_screen_lock:
        _cached_screen = None


def run_bot(game_code, username):
    global bot_status, bot_instance
    bot_status["running"] = True
    bot_status["message"] = "Starting bot..."
    bot_status["game_mode"] = ""
    bot_status["questions_learned"] = 0
    try:
        # 1. Create browser (fast, ~1 s). Set bot_instance immediately so
        #    /screenshot and /send_key work before the game loop starts.
        instance = GimkitBot(status_callback=update_status)
        with _bot_lock:
            bot_instance = instance

        # 2. Start the screenshot cache thread — runs parallel to the game loop.
        t = threading.Thread(target=_screenshot_worker, args=(instance,), daemon=True)
        t.start()

        # 3. Join the game and run the infinite game loop.
        instance.run(game_code, username)
    except Exception as e:
        bot_status["message"] = f"Error: {str(e)}"
    finally:
        bot_status["running"] = False
        with _bot_lock:
            bot_instance = None


def update_status(msg):
    bot_status["message"] = msg
    bot_status["questions_learned"] = len(questions)
    if msg.startswith("[") and "]" in msg:
        bot_status["game_mode"] = msg[1:msg.index("]")]
    elif "Mode:" in msg:
        try:
            bot_status["game_mode"] = msg.split("Mode:")[1].split("—")[0].strip()
        except Exception:
            pass


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global bot_thread, bot_instance
    data      = request.get_json()
    game_code = data.get("game_code", "").strip()
    username  = data.get("username", "").strip()

    if not game_code:
        return jsonify({"success": False, "error": "Please enter a game code."})
    if not username:
        return jsonify({"success": False, "error": "Please enter a username."})
    if len(username) > 20:
        return jsonify({"success": False, "error": "Username must be 20 characters or fewer."})
    if bot_status["running"]:
        return jsonify({"success": False, "error": "Bot is already running."})

    bot_thread = threading.Thread(target=run_bot, args=(game_code, username), daemon=True)
    bot_thread.start()
    return jsonify({"success": True})


@app.route("/reset", methods=["POST"])
def reset():
    global bot_status, bot_instance
    bot_status["running"] = False
    bot_status["message"] = "Idle"
    bot_status["game_mode"] = ""
    bot_status["questions_learned"] = 0
    with _bot_lock:
        if bot_instance:
            try:
                bot_instance.driver.quit()
            except Exception:
                pass
            bot_instance = None
    with _cached_screen_lock:
        global _cached_screen
        _cached_screen = None
    return jsonify({"success": True})


@app.route("/status")
def status():
    return jsonify(bot_status)


# ── Live view ─────────────────────────────────────────────────────────────────

@app.route("/screenshot")
def screenshot():
    """Return the latest cached browser JPEG — always fast, never blocks."""
    # Serve from cache (updated by background thread)
    with _cached_screen_lock:
        cached = _cached_screen

    if cached:
        return Response(cached, mimetype="image/jpeg",
                        headers={"Cache-Control": "no-store"})

    # Bot not running or cache not yet populated — return placeholder
    return Response(_placeholder_image(), mimetype="image/jpeg",
                    headers={"Cache-Control": "no-store"})


def _placeholder_image():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (1280, 720), (20, 20, 35))
    d   = ImageDraw.Draw(img)
    d.text((540, 340), "Bot not running", fill=(80, 80, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=60)
    return buf.getvalue()


@app.route("/send_key", methods=["POST"])
def send_key():
    """Forward a key press into the bot's browser via JS dispatchEvent."""
    with _bot_lock:
        inst = bot_instance
    if not inst:
        return jsonify({"ok": False, "reason": "bot not running"})
    data = request.get_json(silent=True) or {}
    key  = data.get("key", "")
    try:
        from Main import KEY_MAP, JS_FIRE_KEY
        code, key_code = KEY_MAP.get(key, (key, ord(key) if len(key) == 1 else 0))
        call = f"({JS_FIRE_KEY})(arguments[0], arguments[1], arguments[2], arguments[3])"
        inst.driver.execute_script(call, key, code, key_code, "keydown")
        time.sleep(0.08)
        inst.driver.execute_script(call, key, code, key_code, "keyup")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "reason": str(e)})


@app.route("/send_click", methods=["POST"])
def send_click():
    """Forward a click at (x, y) into the bot's browser."""
    with _bot_lock:
        inst = bot_instance
    if not inst:
        return jsonify({"ok": False, "reason": "bot not running"})
    data = request.get_json(silent=True) or {}
    x    = int(data.get("x", 0))
    y    = int(data.get("y", 0))
    try:
        inst.driver.execute_script(
            "document.elementFromPoint(arguments[0],arguments[1])?.click();", x, y)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "reason": str(e)})


# ── Debug routes ──────────────────────────────────────────────────────────────

@app.route("/debug")
def debug_index():
    pngs   = sorted(glob.glob("/tmp/step*.png") + glob.glob("/tmp/fail_*.png")
                    + glob.glob("/tmp/gameplay*.png"))
    labels = sorted(set(os.path.splitext(os.path.basename(f))[0] for f in pngs))
    rows   = "".join(
        f'<a href="/debug/{l}" style="display:block;margin:8px 0;color:#7c3aed">'
        f'<img src="/debug/{l}" style="width:320px;border:1px solid #333;border-radius:6px;'
        f'vertical-align:middle;margin-right:8px">{l}</a>'
        for l in labels
    )
    return (
        '<html><body style="background:#0f0f1a;color:#ccc;font-family:sans-serif;padding:20px">'
        f'<h2 style="margin-bottom:16px">Debug Snapshots</h2>'
        f'{rows or "<p>No snapshots yet — run the bot first.</p>"}'
        '</body></html>'
    ), 200


@app.route("/debug/<label>")
def debug_file(label):
    for ext, mime in [(".png", "image/png"), (".html", "text/html")]:
        path = f"/tmp/{label}{ext}"
        if os.path.exists(path):
            return send_file(path, mimetype=mime)
    return f"No debug file found for '{label}'", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
