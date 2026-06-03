"""
Tool 1: Facebook Link to UID / Phone Number Converter
Supports multiple Facebook URL formats and batch processing.
"""

import re
import json
import requests
from urllib.parse import urlparse, parse_qs


# ──────────────────────────────────────────────
#  Facebook Link → UID Converter
# ──────────────────────────────────────────────

def extract_uid_from_url(url: str) -> dict:
    """
    Extract UID or username from a Facebook URL.

    Supported formats:
      - https://www.facebook.com/profile.php?id=100012345678901
      - https://www.facebook.com/100012345678901
      - https://www.facebook.com/username
      - https://fb.com/100012345678901
      - https://m.facebook.com/username
      - https://www.facebook.com/people/name/100012345678901

    Returns a dict with keys: url, uid, username, type, error
    """
    result = {
        "url": url.strip(),
        "uid": None,
        "username": None,
        "type": None,
        "error": None,
    }

    url_clean = url.strip()

    # Remove trailing slashes
    url_clean = url_clean.rstrip("/")

    try:
        parsed = urlparse(url_clean)
    except Exception:
        result["error"] = "Invalid URL"
        return result

    # Check it's a Facebook domain
    valid_domains = [
        "facebook.com", "www.facebook.com", "m.facebook.com",
        "fb.com", "www.fb.com", "web.facebook.com",
    ]
    if parsed.hostname not in valid_domains:
        result["error"] = f"Not a Facebook URL (domain: {parsed.hostname})"
        return result

    path = parsed.path

    # ── Pattern 1: /profile.php?id=XXXXX ──────────────────────────────
    if "profile.php" in path:
        query = parse_qs(parsed.query)
        if "id" in query:
            uid = query["id"][0]
            result["uid"] = uid
            result["type"] = "numeric_id"
            return result
        else:
            result["error"] = "No 'id' parameter found in profile.php URL"
            return result

    # ── Pattern 2: /people/name/XXXXX ─────────────────────────────────
    people_match = re.search(r"/people/[^/]+/(\d+)", path)
    if people_match:
        result["uid"] = people_match.group(1)
        result["type"] = "numeric_id"
        return result

    # ── Pattern 3: /{numeric_id} ──────────────────────────────────────
    numeric_match = re.match(r"^/(\d{5,})$", path)
    if numeric_match:
        result["uid"] = numeric_match.group(1)
        result["type"] = "numeric_id"
        return result

    # ── Pattern 4: /{username} ────────────────────────────────────────
    username_match = re.match(r"^/([a-zA-Z0-9.]+)$", path)
    if username_match:
        username = username_match.group(1)
        # Skip known non-profile paths
        reserved = [
            "login", "logout", "register", "settings", "help",
            "policies", "pages", "groups", "events", "photos",
            "videos", "marketplace", "gaming", "watch", "stories",
            "reels", "ads", "business", "developers", "about",
        ]
        if username.lower() in reserved:
            result["error"] = f"'/{username}' is a reserved Facebook path, not a profile"
            return result
        result["username"] = username
        result["type"] = "username"
        return result

    result["error"] = "Could not parse UID or username from URL"
    return result


def resolve_username_to_uid(username: str, access_token: str = None) -> dict:
    """
    Attempt to resolve a Facebook username to a numeric UID
    using the Facebook Graph API (requires a valid access token).

    Returns dict with keys: username, uid, error
    """
    result = {"username": username, "uid": None, "error": None}

    if not access_token:
        result["error"] = (
            "No access token provided. "
            "To resolve usernames to UIDs you need a Facebook Graph API access token.\n"
            "Get one at: https://developers.facebook.com/tools/explorer/"
        )
        return result

    api_url = f"https://graph.facebook.com/v19.0/{username}"
    params = {
        "fields": "id,name",
        "access_token": access_token,
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        data = response.json()
        if "id" in data:
            result["uid"] = data["id"]
        else:
            error_msg = data.get("error", {}).get("message", "Unknown API error")
            result["error"] = error_msg
    except requests.exceptions.RequestException as exc:
        result["error"] = f"Request failed: {exc}"

    return result


def extract_phone_from_text(text: str) -> list:
    """
    Extract phone numbers that may appear alongside a Facebook link
    (e.g. in pasted account data: 'fb.com/uid  +1234567890').

    Supports formats:
      +1 234 567 8901, (123) 456-7890, 1234567890, +84xxxxxxxxx, etc.
    """
    phone_pattern = re.compile(
        r"(?:\+?\d{1,3}[\s\-]?)?"   # country code
        r"(?:\(?\d{2,4}\)?[\s\-]?)?" # area code
        r"\d{3,4}[\s\-]?"            # first group
        r"\d{3,4}[\s\-]?"            # second group
        r"\d{0,4}"                   # optional third group
    )
    matches = phone_pattern.findall(text)
    # Filter: only keep matches that have at least 7 digits total
    phones = []
    for m in matches:
        digits_only = re.sub(r"\D", "", m)
        if 7 <= len(digits_only) <= 15:
            phones.append(m.strip())
    # De-duplicate while preserving order
    seen = set()
    unique = []
    for p in phones:
        key = re.sub(r"\D", "", p)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


# ──────────────────────────────────────────────
#  Interactive CLI for Tool 1
# ──────────────────────────────────────────────

def print_banner():
    print()
    print("=" * 62)
    print("   TOOL 1 — Facebook Link → UID / Phone Number Converter")
    print("=" * 62)


def run_tool1():
    print_banner()
    print()
    print("  Options:")
    print("    [1]  Convert a single Facebook link")
    print("    [2]  Batch convert (multiple links, one per line)")
    print("    [3]  Resolve username → UID  (needs Graph API token)")
    print("    [4]  Extract phone numbers from text block")
    print("    [0]  Back to main menu")
    print()

    choice = input("  Select option: ").strip()

    if choice == "1":
        convert_single_link()
    elif choice == "2":
        convert_batch_links()
    elif choice == "3":
        resolve_username_mode()
    elif choice == "4":
        extract_phone_mode()
    elif choice == "0":
        return
    else:
        print("  [!] Invalid option.")
        input("  Press Enter to continue...")

    run_tool1()   # loop back


def convert_single_link():
    print()
    url = input("  Paste Facebook link: ").strip()
    if not url:
        print("  [!] No URL provided.")
        input("  Press Enter to continue...")
        return

    result = extract_uid_from_url(url)
    print()
    print("  ── Result ──────────────────────────────────────")
    if result["error"]:
        print(f"  [ERROR]  {result['error']}")
    else:
        if result["uid"]:
            print(f"  UID      : {result['uid']}")
        if result["username"]:
            print(f"  Username : {result['username']}")
        print(f"  Type     : {result['type']}")
    print("  ────────────────────────────────────────────────")
    print()

    # Also scan for phone numbers in the same text
    phones = extract_phone_from_text(url)
    if phones:
        print(f"  Phone numbers found in input: {', '.join(phones)}")
        print()

    input("  Press Enter to continue...")


def convert_batch_links():
    print()
    print("  Paste Facebook links (one per line). Type 'done' on a new line to finish:")
    lines = []
    while True:
        line = input("    > ").strip()
        if line.lower() in ("done", "exit", "quit", ""):
            if lines:
                break
            print("    (blank line ignored — paste links or type 'done')")
            continue
        lines.append(line)

    print()
    print("  ── Batch Results ─────────────────────────────────────────────────────")
    print(f"  {'#':<4} {'Input URL':<45} {'UID / Username':<20} {'Status'}")
    print("  " + "-" * 80)

    for idx, url in enumerate(lines, start=1):
        result = extract_uid_from_url(url)
        if result["error"]:
            display_id = "—"
            status = f"ERROR: {result['error']}"
        else:
            display_id = result["uid"] or result["username"] or "—"
            status = result["type"]
        url_short = url[:42] + "..." if len(url) > 45 else url
        print(f"  {idx:<4} {url_short:<45} {display_id:<20} {status}")

    print("  " + "-" * 80)
    print()

    # Export option
    export = input("  Export results to JSON? (y/n): ").strip().lower()
    if export == "y":
        filename = input("  Filename [fb_uid_results.json]: ").strip() or "fb_uid_results.json"
        results = [extract_uid_from_url(u) for u in lines]
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  [✓] Saved to {filename}")
        except OSError as e:
            print(f"  [!] Could not save: {e}")
    print()
    input("  Press Enter to continue...")


def resolve_username_mode():
    print()
    print("  NOTE: Resolving usernames to numeric UIDs requires a Facebook Graph API token.")
    print("  Get one at: https://developers.facebook.com/tools/explorer/")
    print()
    token = input("  Paste your access token: ").strip()
    if not token:
        print("  [!] No token provided.")
        input("  Press Enter to continue...")
        return

    print()
    print("  Enter usernames (one per line). Type 'done' to finish:")
    usernames = []
    while True:
        u = input("    > ").strip()
        if u.lower() in ("done", "exit", "quit", ""):
            if usernames:
                break
            continue
        usernames.append(u)

    print()
    print("  ── Resolution Results ──────────────────────────────────────")
    for uname in usernames:
        res = resolve_username_to_uid(uname, token)
        if res["uid"]:
            print(f"  {res['username']:<30} → UID: {res['uid']}")
        else:
            print(f"  {res['username']:<30} → ERROR: {res['error']}")
    print("  " + "-" * 60)
    print()
    input("  Press Enter to continue...")


def extract_phone_mode():
    print()
    print("  Paste text block (may contain phone numbers). Type 'done' on a new line:")
    lines = []
    while True:
        line = input("    > ")
        if line.strip().lower() in ("done",):
            break
        lines.append(line)

    full_text = "\n".join(lines)
    phones = extract_phone_from_text(full_text)

    print()
    print("  ── Phone Numbers Found ──────────────────────────")
    if phones:
        for p in phones:
            digits = re.sub(r"\D", "", p)
            print(f"    {p:<25}  (digits: {digits})")
    else:
        print("    No phone numbers detected.")
    print("  " + "-" * 50)
    print()
    input("  Press Enter to continue...")
