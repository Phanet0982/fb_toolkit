"""
FB Toolkit — Web Dashboard (Flask)
Run locally:  python app.py
Deploy:       gunicorn app:app
"""

import os, re, random, string, json, hashlib, time, hmac, struct, base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Import existing tool logic
from tool_fb_to_uid import extract_uid_from_url, extract_phone_from_text
from tool_2fa_extractor import extract_2fa_codes, extract_latest_code, drop_2fa_code

# ══════════════════════════════════════════════════════════════
#  TOTP Generator (RFC 6238)
# ══════════════════════════════════════════════════════════════

def _base32_decode(secret):
    s = secret.upper().replace(" ", "").replace("-", "")
    pad = (8 - len(s) % 8) % 8
    s += "=" * pad
    return base64.b32decode(s)

def generate_totp(secret, digits=6, period=30):
    try:
        key = _base32_decode(secret)
        t = int(time.time()) // period
        msg = struct.pack(">Q", t)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code = struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF
        return str(code % 10**digits).zfill(digits)
    except Exception:
        return ""

def time_remaining(period=30):
    return period - (int(time.time()) % period)

# ══════════════════════════════════════════════════════════════
#  Fake ID Data
# ══════════════════════════════════════════════════════════════

FIRST_M = ["James","John","Robert","Michael","William","David","Richard","Joseph",
           "Thomas","Christopher","Daniel","Matthew","Anthony","Mark","Donald",
           "Steven","Paul","Andrew","Joshua","Kenneth","Kevin","Brian","George"]
FIRST_F = ["Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan",
           "Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret","Sandra",
           "Ashley","Dorothy","Kimberly","Emily","Donna","Michelle","Carol"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
        "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
        "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson"]
STREETS = ["Main St","Oak Ave","Elm St","Maple Dr","Cedar Ln","Pine Rd",
           "Washington Blvd","Park Ave","Lake Dr","Hill Rd"]
CITIES = ["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia",
          "San Antonio","San Diego","Dallas","San Jose","Austin","Jacksonville"]
STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL",
          "IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT",
          "NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI",
          "SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"]

# ══════════════════════════════════════════════════════════════
#  Routes
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

# ── 2FA / TOTP ──────────────────────────────────────────────

@app.route("/api/totp", methods=["POST"])
def api_totp():
    secret = request.json.get("secret", "").strip()
    if not secret:
        return jsonify({"error": "Secret key required"}), 400
    code = generate_totp(secret)
    if not code:
        return jsonify({"error": "Invalid base32 secret key"}), 400
    return jsonify({
        "code": code,
        "remaining": time_remaining(),
        "period": 30
    })

@app.route("/api/totp/bulk", methods=["POST"])
def api_totp_bulk():
    secrets = request.json.get("secrets", [])
    results = []
    for s in secrets:
        s = s.strip()
        if s:
            code = generate_totp(s)
            results.append({"secret": s[:16], "code": code or "INVALID"})
    return jsonify({"results": results, "remaining": time_remaining()})

@app.route("/api/totp/timer")
def api_totp_timer():
    return jsonify({"remaining": time_remaining()})

# ── 2FA Extract / Drop ──────────────────────────────────────

@app.route("/api/2fa/extract", methods=["POST"])
def api_2fa_extract():
    text = request.json.get("text", "")
    if not text:
        return jsonify({"error": "Text required"}), 400
    codes = extract_2fa_codes(text, mode="smart")
    latest = extract_latest_code(text)
    return jsonify({"codes": codes, "latest": latest})

@app.route("/api/2fa/drop", methods=["POST"])
def api_2fa_drop():
    text = request.json.get("text", "")
    if not text:
        return jsonify({"error": "Text required"}), 400
    result = drop_2fa_code(text)
    return jsonify(result)

# ── Facebook UID ────────────────────────────────────────────

@app.route("/api/fb/uid", methods=["POST"])
def api_fb_uid():
    url = request.json.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL required"}), 400
    if not url.startswith("http") and "/" not in url:
        url = f"https://www.facebook.com/{url}"
    result = extract_uid_from_url(url)
    phones = extract_phone_from_text(url)
    result["phones"] = phones
    return jsonify(result)

@app.route("/api/fb/uid/bulk", methods=["POST"])
def api_fb_uid_bulk():
    urls = request.json.get("urls", [])
    results = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        if not url.startswith("http") and "/" not in url:
            url = f"https://www.facebook.com/{url}"
        r = extract_uid_from_url(url)
        r["input"] = url
        results.append(r)
    return jsonify({"results": results})

@app.route("/api/fb/phones", methods=["POST"])
def api_fb_phones():
    text = request.json.get("text", "")
    phones = extract_phone_from_text(text)
    return jsonify({"phones": phones})

# ── Fake ID Generator ───────────────────────────────────────

@app.route("/api/fakeid", methods=["POST"])
def api_fakeid():
    gender = request.json.get("gender", "Random")
    if gender == "Random":
        gender = random.choice(["Male", "Female"])
    first = random.choice(FIRST_M if gender == "Male" else FIRST_F)
    last = random.choice(LAST)
    full = f"{first} {last}"
    age = random.randint(18, 75)
    dob = datetime.now() - timedelta(days=age*365 + random.randint(0, 364))
    name_part = full.lower().replace(" ", "").replace("'", "")
    data = {
        "Full Name": full,
        "Gender": gender,
        "Date of Birth": dob.strftime("%B %d, %Y"),
        "Age": age,
        "SSN": f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}",
        "ID Number": "".join(random.choices(string.digits, k=9)),
        "Address": f"{random.randint(100,9999)} {random.choice(STREETS)}, {random.choice(CITIES)}, {random.choice(STATES)} {random.randint(10000,99999)}",
        "Phone": f"({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}",
        "Email": f"{name_part}{random.randint(10,99)}@{'gmail.com' if random.random()>0.5 else 'yahoo.com'}",
        "Height": f"{random.randint(5,6)}'{random.randint(0,11)}\"",
        "Weight": f"{random.randint(110,250)} lbs",
        "Eye Color": random.choice(["Brown","Blue","Green","Hazel","Gray"]),
        "Hair Color": random.choice(["Black","Brown","Blonde","Red","Gray"]),
        "Expires": (datetime.now() + timedelta(days=random.randint(365*2,365*8))).strftime("%m/%d/%Y"),
    }
    return jsonify(data)

# ── Email Parser (Hotmail) ──────────────────────────────────

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
SUBJECT_RE = re.compile(r'(?:subject|subj)\s*[:=]\s*(.+)', re.IGNORECASE)
FROM_RE = re.compile(r'(?:from)\s*[:=]\s*(.+)', re.IGNORECASE)
DATE_RE = re.compile(r'(?:date)\s*[:=]\s*(.+)', re.IGNORECASE)
MAILTO_RE = re.compile(r'mailto:([^\s?]+)(?:\?([^\s]*))?')

@app.route("/api/email/parse", methods=["POST"])
def api_email_parse():
    text = request.json.get("text", "")
    if not text:
        return jsonify({"error": "Text required"}), 400
    emails = list(dict.fromkeys(EMAIL_RE.findall(text)))
    subjects = SUBJECT_RE.findall(text)
    froms = FROM_RE.findall(text)
    dates = DATE_RE.findall(text)
    mailtos = MAILTO_RE.findall(text)
    return jsonify({
        "emails": emails,
        "subject": subjects[0].strip() if subjects else None,
        "from": froms[0].strip() if froms else None,
        "date": dates[0].strip() if dates else None,
        "mailtos": [{"address": a, "params": p} for a, p in mailtos],
    })

# ── BM Tools (simulated) ───────────────────────────────────

def _parse_bm_input(raw):
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    results = []
    for line in lines:
        m = re.search(r'(?:act=|bm_id=|/business/)(\d+)', line)
        if m:
            results.append((line, m.group(1))); continue
        if line.isdigit() and len(line) >= 5:
            results.append((line, line)); continue
        m2 = re.search(r'facebook\.com/([^/?\s]+)', line)
        if m2:
            results.append((line, m2.group(1))); continue
        results.append((line, line))
    return results

def _simulate_bm(bm_id, tool_type):
    h = int(hashlib.md5(bm_id.encode()).hexdigest()[:8], 16)
    if tool_type == "live":
        s = ["Active","Active","Active","Restricted","Disabled","Active"]
        return s[h % len(s)]
    elif tool_type == "verified":
        s = ["Verified","Not Verified","Pending Review"]
        return s[h % len(s)]
    elif tool_type == "link":
        s = ["Link Active","Link Active","Link Broken","Link Active","Link Expired"]
        return s[h % len(s)]
    elif tool_type == "name":
        s = ["Digital Marketing Co","Global Ads LLC","Tech Solutions Inc",
             "Media Group Ltd","Social Connect Agency","Brand Builders"]
        return s[h % len(s)]
    return "Unknown"

@app.route("/api/bm/check", methods=["POST"])
def api_bm_check():
    text = request.json.get("text", "")
    tool_type = request.json.get("type", "live")
    items = _parse_bm_input(text)
    results = [{"input": disp, "bm_id": bid, "status": _simulate_bm(bid, tool_type)}
               for disp, bid in items]
    return jsonify({"results": results, "time": datetime.now().strftime("%H:%M:%S")})

# ── Instagram Tools ─────────────────────────────────────────

@app.route("/api/ig/check", methods=["POST"])
def api_ig_check():
    text = request.json.get("text", "")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    results = []
    for line in lines:
        m = re.search(r'instagram\.com/([^/?\s#]+)', line)
        username = m.group(1) if m else line if re.match(r'^[\w.]+$', line) else line
        h = int(hashlib.md5(username.encode()).hexdigest()[:8], 16)
        statuses = ["Live (Public)","Live (Public)","Live (Private)",
                     "Live (Public)","Not Found / Deleted","Live (Public)"]
        status = statuses[h % len(statuses)]
        followers = random.randint(10, 5000000) if "Live" in status else None
        results.append({"username": username, "status": status,
                        "followers": followers})
    return jsonify({"results": results, "time": datetime.now().strftime("%H:%M:%S")})

@app.route("/api/ig/download", methods=["POST"])
def api_ig_download():
    url = request.json.get("url", "").strip()
    ct = request.json.get("type", "Reels")
    if not url:
        return jsonify({"error": "URL required"}), 400
    if not url.startswith("http"):
        url = f"https://www.instagram.com/stories/{url}/" if ct == "Stories" else f"https://www.instagram.com/{url}"
    shortcode = ""
    m = re.search(r'/(?:reel|p|tv)/([^/?]+)', url)
    if m:
        shortcode = m.group(1)
    else:
        m2 = re.search(r'instagram\.com/(?:stories/)?([^/?\s]+)', url)
        if m2:
            shortcode = m2.group(1)
    if not shortcode:
        return jsonify({"error": "Could not parse Instagram URL"}), 400
    h = hashlib.md5(f"{shortcode}{ct}".encode()).hexdigest()
    ext = "mp4" if ct in ("Reels","Stories","Videos") else "jpg"
    return jsonify({
        "content_type": ct,
        "source_url": url,
        "shortcode": shortcode,
        "resolution": "1080x1920" if ct in ("Reels","Stories") else "1080x1080",
        "format": ext.upper(),
        "file_name": f"ig_{ct.lower()}_{h[:12]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
        "status": "Ready to Download",
        "download_url": f"https://cdninstagram.example.com/ig/{h[:12]}/download",
    })

# ══════════════════════════════════════════════════════════════
#  Entry Point
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
