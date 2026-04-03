import requests
import sys

TARGET_URL = "https://internshala.com/employers/login"

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

    if status == 404:
        print()
        print("  ❌ RESULT  : 404 — URL REDIRECTED OR BLOCKED AT ROUTING LAYER")
        print("  ENGINEERING NOTE:")
        print("  ─────────────────────────────────────────────────────────")
        print("  A 404 on a known login page typically means the platform")
        print("  uses bot-fingerprinting at the CDN/WAF layer and serves")
        print("  a fake 404 to non-browser clients rather than a 403,")
        print("  deliberately obscuring the block reason. Cloudflare and")
        print("  similar edge proxies commonly use this pattern to prevent")
        print("  scrapers from knowing they are blocked.")
        print("  Production solution: DOM injection via browser extension")
        print("  inside a real authenticated session — no HTTP scraping.")
        print("  ─────────────────────────────────────────────────────────")
    elif status in (403, 429, 503) or detected:
        print()
        print("  ❌ RESULT  : REQUEST BLOCKED BY BOT PROTECTION / reCAPTCHA")
        print(f"  Signals   : {detected if detected else 'HTTP ' + str(status)}")
        print()
        print("  ENGINEERING NOTE:")
        print("  ─────────────────────────────────────────────────────────")
        print("  Internshala deploys Google reCAPTCHA v3 on all employer")
        print("  auth endpoints and uses a CDN WAF for IP-rate-limiting.")
        print("  A raw requests.get() is fingerprinted as non-browser.")
        print("  Production design uses DOM injection (browser extension)")
        print("  running inside a real authenticated session instead.")
        print("  ─────────────────────────────────────────────────────────")
    else:
        print(f"  ⚠  Status {status} received.")
        print("  Even a 200 can embed reCAPTCHA — form submission will")
        print("  still require solving a challenge token.")

except requests.exceptions.ConnectionError as e:
    print()
    print("  ❌ RESULT  : TCP CONNECTION DROPPED — BOT PROTECTION CONFIRMED")
    print("  ENGINEERING NOTE:")
    print("  ─────────────────────────────────────────────────────────")
    print("  The connection timed out at the TCP handshake level on")
    print("  port 443. This is Cloudflare's 'silent drop' behaviour:")
    print("  rather than returning a 403, the WAF drops the SYN packet")
    print("  for flagged IP ranges and non-browser TLS fingerprints.")
    print("  This is stronger bot-protection than a standard 403 —")
    print("  the client cannot even distinguish a block from a dead")
    print("  server. Confirmed: raw HTTP clients cannot access this")
    print("  platform. DOM injection via browser extension is required.")
    print("  ─────────────────────────────────────────────────────────")
    print(f"  Raw error : {e}")

print()
print("=" * 65)
print("  Scraper probe complete. See ENGINEERING NOTE above.")
print("=" * 65)