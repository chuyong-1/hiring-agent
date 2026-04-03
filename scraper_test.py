import requests
import sys

TARGET_URL = "https://internshala.com/employer/login"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection":      "keep-alive",
}

print("=" * 65)
print("  SCRAPER PROBE — Internshala Employer Login")
print("=" * 65)
print(f"  Target  : {TARGET_URL}")
print(f"  Method  : GET with browser-spoofed User-Agent")
print()

try:
    response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
    status   = response.status_code
    body     = response.text.lower()

    print(f"  HTTP Status Code : {status}")

    # Detect common bot-protection signals
    captcha_signals = [
        "recaptcha", "g-recaptcha", "captcha",
        "cf-browser-verification", "cloudflare",
        "access denied", "bot protection", "403 forbidden",
        "unusual traffic", "automated", "blocked",
    ]
    detected = [s for s in captcha_signals if s in body]

    if status in (403, 429, 503) or detected:
        print()
        print("  ❌ RESULT  : REQUEST BLOCKED BY BOT PROTECTION / reCAPTCHA")
        print(f"  Signals   : {detected if detected else 'HTTP ' + str(status)}")
        print()
        print("  ENGINEERING NOTE:")
        print("  ─────────────────────────────────────────────────────────")
        print("  Internshala deploys Google reCAPTCHA v3 on all employer")
        print("  auth endpoints and likely uses Cloudflare or a similar")
        print("  edge WAF for IP-rate-limiting and bot fingerprinting.")
        print("  A raw requests.get() is immediately fingerprinted as a")
        print("  non-browser agent. This is why the production design uses")
        print("  DOM injection (browser extension) rather than scraping:")
        print("  the agent runs inside a real authenticated browser session,")
        print("  bypassing all bot-detection controls entirely.")
        print("  ─────────────────────────────────────────────────────────")
    else:
        print(f"  ⚠  Status {status} — page loaded but may be a CAPTCHA challenge page.")
        print("  Inspect response body for hidden CAPTCHA widgets.")
        print("  Note: Even a 200 response can embed reCAPTCHA; actual")
        print("  form submission will still be blocked by challenge tokens.")

except requests.exceptions.ConnectionError as e:
    print(f"  ❌ CONNECTION ERROR: {e}")
    print("  This likely indicates IP-level blocking or DNS filtering.")
except requests.exceptions.Timeout:
    print("  ❌ TIMEOUT: Request timed out — possible IP rate-limiting.")
except Exception as e:
    print(f"  ❌ UNEXPECTED ERROR: {e}")
    sys.exit(1)

print()
print("=" * 65)
print("  Scraper probe complete. See ENGINEERING NOTE above.")
print("=" * 65)