from flask import Flask, request, jsonify, make_response
import jwt
import gzip
import base64
import binascii

app = Flask(__name__)

# =========================
# ⚙️ CONFIG
# =========================
# The secret role the player needs to forge
TARGET_ROLE = "phoenix.elevated.sigil"
XOR_KEY = 0x37

# =========================
# 🔐 REAL PUBLIC KEY (Used for verification)
# =========================
# IMPORTANT: In a real scenario, this must match the key 
# you used to generate the ENCODED_KEY fragments.
REAL_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1vNfL9E7pI8L6Xv3YQ2Bz9P9WkS5L1v7N9pQxR8uY6v4f7n8Q9v5r6t7y8u9w0A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7B8C9D0E1F2G3H4I5J6K7L8M9N0O1P2Q3R4S5T6U7V8W9X0Y1Z2A3B4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0S1T2U3V4W5X6Y7Z8A9B0C1D2E3F4G5H6I7J8K9L0M1N2O3P4Q5R6S7T8U9V0W1X2Y3Z4A5B6C7D8E9F0G1H2I3J4K5L6M7N8O9P0Q1R2S3T4U5V6W7X8Y9Z0A1B2C3D4E5F6G7H8I9J0wIDAQAB
-----END PUBLIC KEY-----"""

# =========================
# 🔁 ENCODED BLOB (Precomputed)
# =========================
# Replace this string with the result of your local encoding script
ENCODED_KEY = r"z`nn]vzsvNzZm_mpfxcvNmZnyc\Nn~m`e^zMvOysfynxcS_zca\xcnzcrn`rzZfx`}]zMfOm]\n]}^ycu^ny]z]u[nM[]zs}[y]~zsrNnZm^mcnm]nmpy[xc[\ms\zc\@msTxpa_y]nzMaZn`zOybzpbyMvOzsvnMa\ycr@zMTm]yZz`fMxcbypzzM__mc\mZzNncnmpy^mcSZn`}[y~MmcTypbycn@zszycTz~y`m]ncP@xpfxc~zcz@xcPncbmZqZzcaZmsm]xsbz`nn]eZmp~Nycu[zcbOms~y`}]ncnym]mc\My]znZ}_zbmcfm]S\yZ~m]~xcvOxcS\ycvzZm[ycPm`q\mZ}]n`m^ms_^ncb@mZm_zcy]n`}_ysnn]e_zM_Zy`rm`nnM~Mm]S\xpnypy_x`z@ybzMrzcPMzs}]yMfxpnysu_m`~n]q[xc~@ms_\ye_nMny`~MzcnNyp~@xcT@zZ}^yc\zfOmsTxsrMzprm`q^zp}]zMfzcfyMzNyc[ZyMu[xcryc}_mpzMncPyZq\zc\m`nyp}]y]e\zbzsqZzsa[x`q[nMPy]e_yp~OxsrOmcPy}\nZf@xpr@zMvyZe]z`rms~xcyZys\mcnncnm`y[nM}\mszy]a_zcvz]n@n`e\nfOnzn][Zm`nms~@n]rycTOzMPycrzsPyc_[n]~nMfyMu_nZ~n]\n`bm]z@yMzOysvn]z@nZm_zse[ncTOxsnOypq^z][\nrnMfmcbOxc\MzMrOzMq[nZr@m]Tzpfms~xsSZxcu[nq^n]rOmsvxsqZycnzMzNxpb@n`y]zsz@y`~Nxsbm`fnM[_zse^mZq]yczMyy]nc}^xsrMy]bmsu^ycrysm\yce^y`~y]\Nyfy]bMy`e\zMv@xsTNz]TNy]y^zsrzcbzMm\nM_[mpm\mcrn]e\nMPz]e^zZa^n]f@zMTzZbmpny]S]xcnMzMzy`mZm]\msvzczxsnycvm]mZna\nZnmcy[yMq^ypnmsu\m`~MxcTzZq_mcPMmpq[xpry`eZnbOnczncS\mZf@nZm\mZrNyby`z@z]v@zsv" 

# Split the blob into three pieces for the hunt
total_len = len(ENCODED_KEY)
FRAG_1 = ENCODED_KEY[:total_len//3]
FRAG_2 = ENCODED_KEY[total_len//3: 2*total_len//3]
FRAG_3 = ENCODED_KEY[2*total_len//3:]

# =========================
# 🧪 JWT GENERATION
# =========================

def generate_token():
    payload = {
        "user": "harry",
        "role": "cruxbreaker",
        "hint": f"The middle gate is locked with: {FRAG_2}"
    }
    # Initial token is signed correctly with RS256
    token = jwt.encode(payload, REAL_PUBLIC_KEY, algorithm="RS256")
    return token

# =========================
# ⚠️ VULNERABLE VERIFY
# =========================

def verify_token(token):
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")

        # 🔥 THE VULNERABILITY: HMAC CONFUSION
        # If the user changes alg to HS256, we mistakenly use 
        # the Public Key string as the HMAC secret.
        if alg == "HS256":
            return jwt.decode(token, REAL_PUBLIC_KEY, algorithms=["HS256"])
        else:
            return jwt.decode(token, REAL_PUBLIC_KEY, algorithms=["RS256"])
    except Exception:
        return None

# =========================
# 🏠 ROUTES
# =========================

@app.route("/")
def home():
    token = generate_token()
    resp = make_response(jsonify({
        "token": token,
        "note": "The Ministry trusts what tokens claim..."
    }))
    # Fragment 1 is hidden in the HTTP Headers
    resp.headers["X-Ministry-Trace"] = FRAG_1
    return resp

@app.route("/static/owl.log")
def static_frag():
    # Fragment 3 is hidden in a "log file"
    return f"archive_fragment={FRAG_3}"

@app.route("/ghost")
def ghost():
    return "Bad Gateway – Ministry node unreachable", 502

@app.route("/vault")
def vault():
    auth = request.headers.get("Authorization")
    if not auth:
        return "Missing token", 401

    token = auth.replace("Bearer ", "")
    data = verify_token(token)

    if not data:
        return "Invalid token", 403

    # Check if the player successfully forged the role
    if data.get("role") == TARGET_ROLE:
        return "Cruxhunt{minist0ry_4c3ss_gr4nt3d}"
    else:
        return f"Access denied. Role '{data.get('role')}' is unauthorized.", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)