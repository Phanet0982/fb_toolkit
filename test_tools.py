"""
Quick unit tests — run with:  python test_tools.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tool_fb_to_uid    import extract_uid_from_url, extract_phone_from_text
from tool_2fa_extractor import extract_2fa_codes, extract_latest_code, drop_2fa_code

passed = 0
failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}")


print("\n" + "=" * 60)
print("  TOOL 1 — Facebook Link → UID  Tests")
print("=" * 60)

# Numeric ID from profile.php
r = extract_uid_from_url("https://www.facebook.com/profile.php?id=100012345678901")
check("profile.php?id=  → uid",       r["uid"] == "100012345678901")
check("profile.php?id=  → type",      r["type"] == "numeric_id")
check("profile.php?id=  → no error",  r["error"] is None)

# Direct numeric path
r = extract_uid_from_url("https://www.facebook.com/100098765432101")
check("fb.com/NUMERIC   → uid",       r["uid"] == "100098765432101")

# Username path
r = extract_uid_from_url("https://www.facebook.com/john.doe")
check("fb.com/username  → username",  r["username"] == "john.doe")
check("fb.com/username  → type",      r["type"] == "username")
check("fb.com/username  → uid=None",  r["uid"] is None)

# /people/ path
r = extract_uid_from_url("https://www.facebook.com/people/Jane-Smith/100087654321098")
check("/people/name/ID  → uid",       r["uid"] == "100087654321098")

# Mobile domain
r = extract_uid_from_url("https://m.facebook.com/profile.php?id=999888777666")
check("m.facebook.com   → uid",       r["uid"] == "999888777666")

# fb.com short domain
r = extract_uid_from_url("https://fb.com/some.user")
check("fb.com/user      → username",  r["username"] == "some.user")

# Reserved path (should error)
r = extract_uid_from_url("https://www.facebook.com/login")
check("reserved /login  → error",     r["error"] is not None)

# Non-Facebook domain (should error)
r = extract_uid_from_url("https://www.google.com/search?q=fb")
check("non-FB domain    → error",     r["error"] is not None)

# Trailing slash
r = extract_uid_from_url("https://www.facebook.com/100011122233344/")
check("trailing slash   → uid",       r["uid"] == "100011122233344")

# Phone number extraction
phones = extract_phone_from_text("fb.com/123456  +1 555-123-4567  contact me")
check("phone +1 555... detected",     len(phones) >= 1)
check("phone contains 5551234567",    any("5551234567" in p.replace("-","").replace(" ","") for p in phones))

print()
print("=" * 60)
print("  TOOL 2 — 2FA Code Extractor  Tests")
print("=" * 60)

# HIGH confidence — Facebook SMS
text1 = "Facebook: Your security code is 847293. Do not share this code."
codes1 = extract_2fa_codes(text1, mode="smart")
check("FB SMS → finds code",           any(c["code"] == "847293" for c in codes1))
check("FB SMS → HIGH confidence",      any(c["confidence"] == "HIGH" for c in codes1 if c["code"] == "847293"))

# MEDIUM confidence — standalone
text2 = "Your code: 519284"
codes2 = extract_2fa_codes(text2, mode="smart")
check("standalone code → found",       any(c["code"] == "519284" for c in codes2))

# Google 2FA
text3 = "G-123456 is your Google verification code."
codes3 = extract_2fa_codes(text3, mode="smart")
check("Google code → found",           any(c["code"] == "123456" for c in codes3))

# Multiple codes in one message
text4 = "First: 111222. Then Facebook sent 333444. Also try 555666"
codes4 = extract_2fa_codes(text4, mode="all")
check("multi codes → finds ≥2",        len(codes4) >= 2)

# extract_latest_code
latest = extract_latest_code(text1)
check("latest code from FB SMS",       latest == "847293")

# drop_2fa_code
result = drop_2fa_code("Your code is 847293 please enter it now")
check("drop → code removed",           "847293" not in result["cleaned_text"])
check("drop → code in removed list",   "847293" in result["removed_codes"])

# No code present
text_empty = "Hello, how are you today?"
codes_empty = extract_2fa_codes(text_empty, mode="smart")
check("no code → empty list",          len(codes_empty) == 0)

# Instagram
text_ig = "Instagram: 748392 is your confirmation code."
codes_ig = extract_2fa_codes(text_ig, mode="smart")
check("Instagram code → found",        any(c["code"] == "748392" for c in codes_ig))

print()
print("=" * 60)
print(f"  RESULTS:  {passed} passed  |  {failed} failed")
print("=" * 60)
print()
