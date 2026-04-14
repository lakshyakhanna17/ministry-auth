from flask import Flask, request, jsonify, make_response
import jwt
import gzip
import base64
import binascii

app = Flask(__name__)

# =========================
# ⚙️ CONFIG
# =========================

TARGET_ROLE = "phoenix.elevated.sigil"
XOR_KEY = 0x37

# =========================
# 🔐 REAL PUBLIC KEY (USED INTERNALLY ONLY)
# =========================

REAL_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALe1pLQ6o+...
-----END PUBLIC KEY-----"""

# =========================
# 🔁 ENCODING PIPELINE (OFFLINE RESULT)
# =========================
# (You would generate this offline — here it's precomputed)

ENCODED_KEY = "4f2a7b8c9d..."  # <-- replace with your final encoded blob

# =========================
# 🧩 SPLIT INTO FRAGMENTS
# =========================

FRAG_1 = ENCODED_KEY[:len(ENCODED_KEY)//3]
FRAG_2 = ENCODED_KEY[len(ENCODED_KEY)//3: 2*len(ENCODED_KEY)//3]
FRAG_3 = ENCODED_KEY[2*len(ENCODED_KEY)//3:]

# =========================
# 🧪 JWT TOKEN (INITIAL)
# =========================

def generate_token():
    payload = {
        "user": "harry",
        "role": "cruxbreaker",
        "hint": "fragment_2"
    }

    token = jwt.encode(payload, REAL_PUBLIC_KEY, algorithm="RS256")
    return token

# =========================
# ⚠️ VULNERABLE VERIFY
# =========================

def verify_token(token):
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")

        # 🔥 VULNERABILITY
        if alg == "HS256":
            # using PUBLIC KEY as HMAC secret
            return jwt.decode(token, REAL_PUBLIC_KEY, algorithms=["HS256"])

        else:
            return jwt.decode(token, REAL_PUBLIC_KEY, algorithms=["RS256"])

    except:
        return None

# =========================
# 🏠 ROOT ENDPOINT
# =========================

@app.route("/")
def home():
    token = generate_token()

    resp = make_response(jsonify({
        "token": token,
        "note": "The Ministry trusts what tokens claim..."
    }))

    # 🔹 embed fragment in header
    resp.headers["X-Ministry-Trace"] = FRAG_1

    return resp

# =========================
# 📁 STATIC FRAGMENT
# =========================

@app.route("/static/owl.log")
def static_frag():
    return f"archive_fragment={FRAG_3}"

# =========================
# 👻 FAKE DEAD END
# =========================

@app.route("/ghost")
def ghost():
    return "Bad Gateway – Ministry node unreachable", 502

# =========================
# 🔐 VAULT (FLAG)
# =========================

@app.route("/vault")
def vault():
    auth = request.headers.get("Authorization")

    if not auth:
        return "Missing token", 401

    token = auth.replace("Bearer ", "")
    data = verify_token(token)

    if not data:
        return "Invalid token", 403

    if data.get("role") == TARGET_ROLE:
        return "Cruxhunt{minist0ry_4c3ss_gr4nt3d}"
    else:
        return "Access denied", 403


# =========================
# 🚀 RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)