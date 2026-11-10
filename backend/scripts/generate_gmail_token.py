"""
CampusFlow — Google OAuth2 Refresh Token Generator
Run this script once locally to authorize your college Gmail account.
"""
import http.server
import json
import os
import urllib.parse
import urllib.request
import webbrowser
import sys

# Load from environment variables or arguments to prevent committing secrets to source control
CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")

if not CLIENT_ID or not CLIENT_SECRET:
    if len(sys.argv) >= 3:
        CLIENT_ID = sys.argv[1]
        CLIENT_SECRET = sys.argv[2]
    else:
        print("Usage: python generate_gmail_token.py <CLIENT_ID> <CLIENT_SECRET>")
        print("Or set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET environment variables.")
        sys.exit(1)
REDIRECT_URI = "http://127.0.0.1:8085"
SCOPE = "https://www.googleapis.com/auth/gmail.send"

auth_code = None

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family:sans-serif;text-align:center;padding:50px;">
                    <h1 style="color:#16a34a;">Authentication Successful!</h1>
                    <p>Google has authorized CampusFlow. You can close this window now.</p>
                </body>
                </html>
            """)
        else:
            err = params.get("error", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h1>Authentication Failed</h1><p>{err}</p>".encode("utf-8"))

    def log_message(self, format, *args):
        pass # Suppress server access logs

def main():
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"response_type=code&"
        f"scope={urllib.parse.quote(SCOPE)}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    print("\n" + "=" * 70)
    print(" CampusFlow Google OAuth2 Authorizer")
    print("=" * 70)
    print("\nOpening your browser to log in with your COLLEGE GOOGLE ACCOUNT...")
    print("\nIf browser doesn't open automatically, copy and paste this URL into your browser:\n")
    print(auth_url)
    print("\n" + "-" * 70)
    print("Waiting for authentication callback on port 8085...")

    server = http.server.HTTPServer(("127.0.0.1", 8085), OAuthCallbackHandler)
    
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    # Wait for the single redirect request
    while not auth_code:
        server.handle_request()

    server.server_close()

    print("\nReceived authorization code from Google! Exchanging for Refresh Token...")

    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            tokens = json.loads(resp.read().decode("utf-8"))
            refresh_token = tokens.get("refresh_token")
            if not refresh_token:
                print("\n[WARNING] No refresh token returned. Did you already authorize previously?")
                print("Google tokens response:", tokens)
                return

            print("\n" + "=" * 70)
            print(" SUCCESS! YOUR GOOGLE REFRESH TOKEN IS:")
            print("=" * 70)
            print(f"\nGMAIL_REFRESH_TOKEN = {refresh_token}\n")
            print("=" * 70)
            
            with open(".gmail_credentials.json", "w") as f:
                json.dump({
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "refresh_token": refresh_token
                }, f, indent=2)
            print("Saved to .gmail_credentials.json")
    except urllib.error.HTTPError as he:
        print("Token exchange failed:", he.code, he.read().decode("utf-8"))
    except Exception as exc:
        print("Token exchange error:", exc)

if __name__ == "__main__":
    main()

