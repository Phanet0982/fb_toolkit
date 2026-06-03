"""
Tool 2: 2FA Code Extractor (Drop 6-digit codes from text)
Detects and extracts 6-digit Two-Factor Authentication codes from any
pasted text — SMS messages, emails, notifications, logs, etc.
"""

import re
import time
import json
from datetime import datetime


# ──────────────────────────────────────────────
#  2FA Code Extraction Engine
# ──────────────────────────────────────────────

# Common 2FA message patterns from known senders
KNOWN_2FA_CONTEXTS = [
    r"facebook", r"meta", r"google", r"instagram", r"twitter",
    r"microsoft", r"apple", r"amazon", r"netflix", r"whatsapp",
    r"telegram", r"discord", r"tiktok", r"snapchat", r"linkedin",
    r"github", r"gitlab", r"binance", r"coinbase", r"paypal",
    r"dropbox", r"slack", r"zoom", r"steam", r"epic.?games",
    r"verification", r"verify", r"security code", r"auth(?:entication)?",
    r"login code", r"otp", r"one.time", r"passcode", r"confirm",
    r"sign.in", r"2fa", r"two.factor", r"mfa",
]

# Build a context-aware regex that looks for 6-digit numbers near 2FA keywords
CONTEXT_PATTERN = re.compile(
    r"(?:" + "|".join(KNOWN_2FA_CONTEXTS) + r")"
    r"[^0-9]{0,60}"            # up to 60 non-digit chars between keyword and code
    r"\b(\d{6})\b",            # the 6-digit code
    re.IGNORECASE,
)

# Standalone 6-digit number (fallback, must be on its own or near punctuation)
STANDALONE_6DIGIT = re.compile(
    r"(?:^|[\s:>\-=(])"       # start of string, whitespace, or common delimiters
    r"(\d{6})"
    r"(?:$|[\s<\-).,!?])",    # end of string, whitespace, or delimiters
    re.MULTILINE,
)

# Generic: any 6-digit number in the text (broadest, lowest confidence)
ANY_6DIGIT = re.compile(r"\b(\d{6})\b")


def extract_2fa_codes(text: str, mode: str = "smart") -> list:
    """
    Extract 6-digit 2FA codes from text.

    Parameters
    ----------
    text : str
        The raw text to scan (SMS, email body, notification, log, etc.)
    mode : str
        Extraction strategy:
          "smart"   — Prioritize codes near known 2FA keywords (most accurate)
          "strict"  — Only return codes found near explicit 2FA context keywords
          "all"     — Return every 6-digit number found (broadest, may have noise)

    Returns
    -------
    list of dict
        Each dict: {code, confidence, context_snippet, position}
    """
    results = []
    seen_codes_at_pos = set()   # track (code, position) to avoid duplicates

    def _add(code: str, confidence: str, start: int):
        key = (code, start)
        if key not in seen_codes_at_pos:
            seen_codes_at_pos.add(key)
            snippet = text[max(0, start - 30): start + 36].replace("\n", " ").strip()
            results.append({
                "code": code,
                "confidence": confidence,
                "context_snippet": snippet,
                "position": start,
            })

    # ── Pass 1: Context-aware match (high confidence) ─────────────────
    for m in CONTEXT_PATTERN.finditer(text):
        _add(m.group(1), "HIGH", m.start(1))

    if mode == "strict":
        return _sort_by_position(results)

    # ── Pass 2: Standalone 6-digit (medium confidence) ────────────────
    for m in STANDALONE_6DIGIT.finditer(text):
        _add(m.group(1), "MEDIUM", m.start(1))

    if mode == "smart":
        return _sort_by_position(results)

    # ── Pass 3: Any 6-digit number (low confidence) ───────────────────
    for m in ANY_6DIGIT.finditer(text):
        _add(m.group(1), "LOW", m.start(1))

    return _sort_by_position(results)


def _sort_by_position(results: list) -> list:
    return sorted(results, key=lambda r: r["position"])


def extract_latest_code(text: str) -> str | None:
    """
    Convenience: return the single most likely 2FA code from text.
    Priority order: HIGH confidence first, then MEDIUM, then LOW.
    Within same confidence, prefer the LAST occurrence (usually the newest).
    """
    codes = extract_2fa_codes(text, mode="smart")
    if not codes:
        return None
    # Sort by confidence priority, then by position descending (latest first)
    priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    codes.sort(key=lambda c: (priority.get(c["confidence"], 3), -c["position"]))
    return codes[0]["code"]


def drop_2fa_code(text: str) -> dict:
    """
    Remove (drop) all detected 6-digit 2FA codes from the input text.
    Returns dict with keys: cleaned_text, removed_codes
    """
    codes_found = extract_2fa_codes(text, mode="all")
    cleaned = text
    removed = []
    for entry in codes_found:
        code = entry["code"]
        cleaned = cleaned.replace(code, "", 1)
        removed.append(code)
    # Clean up extra whitespace left behind
    cleaned = re.sub(r" {2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return {"cleaned_text": cleaned.strip(), "removed_codes": removed}


# ──────────────────────────────────────────────
#  Interactive CLI for Tool 2
# ──────────────────────────────────────────────

def print_banner():
    print()
    print("=" * 62)
    print("   TOOL 2 — 2FA Code Extractor  (drop 6-digit codes)")
    print("=" * 62)


def run_tool2():
    print_banner()
    print()
    print("  Options:")
    print("    [1]  Extract 2FA code from pasted text")
    print("    [2]  Batch extract (multiple messages)")
    print("    [3]  Drop / remove 2FA codes from text")
    print("    [4]  Live clipboard monitor (auto-extract)")
    print("    [5]  Extract from file")
    print("    [0]  Back to main menu")
    print()

    choice = input("  Select option: ").strip()

    if choice == "1":
        single_extract_mode()
    elif choice == "2":
        batch_extract_mode()
    elif choice == "3":
        drop_code_mode()
    elif choice == "4":
        clipboard_monitor_mode()
    elif choice == "5":
        file_extract_mode()
    elif choice == "0":
        return
    else:
        print("  [!] Invalid option.")
        input("  Press Enter to continue...")

    run_tool2()   # loop back


def single_extract_mode():
    print()
    print("  Paste the message / SMS / email text below. Type 'done' on a new line:")
    lines = []
    while True:
        line = input("    > ")
        if line.strip().lower() == "done":
            break
        lines.append(line)

    full_text = "\n".join(lines)
    if not full_text.strip():
        print("  [!] No text provided.")
        input("  Press Enter to continue...")
        return

    codes = extract_2fa_codes(full_text, mode="smart")

    print()
    print("  ── Extracted 2FA Codes ──────────────────────────────────────")
    if codes:
        for i, entry in enumerate(codes, 1):
            tag = {"HIGH": "✓ HIGH", "MEDIUM": "~ MED", "LOW": "? LOW"}
            print(f"    [{i}]  Code: {entry['code']}   Confidence: {tag.get(entry['confidence'], '?')}")
            print(f"         Context: ...{entry['context_snippet']}...")
        latest = extract_latest_code(full_text)
        print()
        print(f"  ► Best match (latest/most likely): {latest}")
    else:
        print("    No 6-digit 2FA codes detected.")
    print("  " + "-" * 60)
    print()
    input("  Press Enter to continue...")


def batch_extract_mode():
    print()
    print("  Paste multiple messages separated by '---' on its own line.")
    print("  Type 'done' on a new line to finish:")
    print()

    messages = []
    current = []
    while True:
        line = input("    > ")
        if line.strip().lower() == "done":
            if current:
                messages.append("\n".join(current))
            break
        if line.strip() == "---":
            if current:
                messages.append("\n".join(current))
                current = []
        else:
            current.append(line)

    print()
    print("  ── Batch Extraction Results ─────────────────────────────────────────")
    for idx, msg in enumerate(messages, 1):
        codes = extract_2fa_codes(msg, mode="smart")
        preview = msg[:60].replace("\n", " ").strip()
        if codes:
            code_str = ", ".join(c["code"] for c in codes)
            print(f"  Msg #{idx}: [{code_str}]  ← {preview}...")
        else:
            print(f"  Msg #{idx}: [NO CODE]       ← {preview}...")
    print("  " + "-" * 70)
    print()
    input("  Press Enter to continue...")


def drop_code_mode():
    print()
    print("  Paste text containing 2FA codes to REMOVE them. Type 'done' on a new line:")
    lines = []
    while True:
        line = input("    > ")
        if line.strip().lower() == "done":
            break
        lines.append(line)

    full_text = "\n".join(lines)
    if not full_text.strip():
        print("  [!] No text provided.")
        input("  Press Enter to continue...")
        return

    result = drop_2fa_code(full_text)

    print()
    print("  ── Result ──────────────────────────────────────────────────")
    if result["removed_codes"]:
        print(f"  Removed codes : {', '.join(result['removed_codes'])}")
    else:
        print("  No 6-digit codes found to remove.")
    print()
    print("  Cleaned text:")
    print("  " + "-" * 50)
    print(f"  {result['cleaned_text']}")
    print("  " + "-" * 50)
    print()
    input("  Press Enter to continue...")


def clipboard_monitor_mode():
    print()
    print("  [!] Clipboard monitor requires 'pyperclip' library.")
    print("      Install with:  pip install pyperclip")
    print()
    try:
        import pyperclip
    except ImportError:
        print("  [!] pyperclip not installed. Falling back to manual paste mode.")
        print("      (Run 'pip install pyperclip' to enable clipboard monitoring)")
        print()
        input("  Press Enter to continue...")
        return

    print("  Monitoring clipboard for 2FA codes... Press Ctrl+C to stop.")
    print("  (Copy any SMS/notification text — codes will auto-extract)")
    print()

    last_clip = ""
    try:
        while True:
            try:
                clip = pyperclip.paste()
            except Exception:
                clip = ""
            if clip and clip != last_clip:
                last_clip = clip
                codes = extract_2fa_codes(clip, mode="smart")
                if codes:
                    ts = datetime.now().strftime("%H:%M:%S")
                    for c in codes:
                        print(f"  [{ts}] ✓ Found code: {c['code']}  (confidence: {c['confidence']})")
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("  Monitor stopped.")
        input("  Press Enter to continue...")


def file_extract_mode():
    print()
    filepath = input("  Enter file path: ").strip()
    if not filepath:
        print("  [!] No path provided.")
        input("  Press Enter to continue...")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"  [!] File not found: {filepath}")
        input("  Press Enter to continue...")
        return
    except OSError as e:
        print(f"  [!] Error reading file: {e}")
        input("  Press Enter to continue...")
        return

    codes = extract_2fa_codes(text, mode="smart")

    print()
    print(f"  ── 2FA Codes found in: {filepath} ──────────────────────────")
    if codes:
        for i, entry in enumerate(codes, 1):
            tag = {"HIGH": "✓ HIGH", "MEDIUM": "~ MED", "LOW": "? LOW"}
            print(f"    [{i}]  Code: {entry['code']}   Confidence: {tag.get(entry['confidence'], '?')}")
            print(f"         Context: ...{entry['context_snippet']}...")
    else:
        print("    No 6-digit 2FA codes found in file.")
    print("  " + "-" * 60)
    print()

    # Export
    export = input("  Export results to JSON? (y/n): ").strip().lower()
    if export == "y":
        out_path = input("  Output filename [2fa_codes_result.json]: ").strip() or "2fa_codes_result.json"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(codes, f, indent=2, ensure_ascii=False)
            print(f"  [✓] Saved to {out_path}")
        except OSError as e:
            print(f"  [!] Could not save: {e}")
    print()
    input("  Press Enter to continue...")
