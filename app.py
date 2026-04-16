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
# 🔐 RSA KEY PAIR
# =========================
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxG24k3W8CDNtgE9alnt2P6PjNDzpxQ/852KcYF7x1uZj+i6z
FT/if7HWA1G9eGpMlpmaA0rC0ca8oj1f+BXmxsCvB0zb3JBHKeSTIfo++EQYY2cO
ovSvrbQCqOqWvbh7ZxWibKMUV2gdoEzG2Ne9jwQh5FH6G3NLVPhjBoOIFG1upnpd
EBQa6OrTY5JbVNySh+zkH1+BlLHJIiyRKB7f7776bTn12hxi5aiL45Ap22LxBoSu
tkQHmUbtHBcFcn9UGN0aJino3jBWQ7xg+lyv77hEqMYZ/LWUK88IaodJpJmSiko+
skeqgPfkDV5dDM6E8aPtaaBxYdNzpX6X3+hT8wIDAQABAoIBAAaWzgo93zQNny64
R4gLIpXsuXWXIk0p+O6jsC5lAPFkgq+k9JaFF7DEFmaMgP6Sq98HzmxhDAf3BeNE
8i/9DBclGSBb9t2ybH1+dv3WY/MpomfM0GdG+sQPT2EhlwAZbPCx5eQfB4YNez27
u/yqJmgVvpoaGRNMQTEO4/awxglpU0dFzbFWTuEAwfiBhWT/hZrZDEyOjc3GBUlX
Znz0TX17ToWzNCE3qc4vBJsb2kKaaBRLmMUVRbBqFQMqsgarTEmVm42V3X51WhYw
fyoWUx/+zXRpQlkqiz3nqk9woqPZbB4cwtfRC3fWbBORI7l9GtfNUS+lzOotx4d8
DmznOwECgYEA6nCm3BCtPSp/kEK4s1wovBY/KUsLjP7aEaWDyTHwLOztiUghImRz
tOlp7v8uGBXJXsrr7R3o5F/l8kazqvNKgCnpaZzI+JVe1StsbLFeFdYqPIlzzwo1
X7XFNOqfGPffDqWh0u+XunQsiyn1tqZyXeHb5MNGBEk2uf1g/Uf40XsCgYEA1n4t
edTUBeHckcscOsaRz6Wht/Df+jrY2df3zKvjs4xp8TbIT2edtSE50P/nl7pAA0rR
vQtbAEeQyla58gATsRUc05CqjEma2Y5Srzuvji9Q2A0GmydneGol7113yO7FU1GN
G3vOe98c3v3RQaszZ1QkJVLQlDmmNv6FoEHxkekCgYEAiXybPn/BORfNS6r1aqpn
cTaSwAK0uXFULfklOj7BHXetLk9Qrzy95qDkcTbRr2pHeAIFLj/WLuhWkCkKgPzA
+jyaGEfMTIw820LmCTBTfvbkOjBZ7FeOSZzuFERsHVZwR8S3DF9aWgx7evmWkhE3
DPvB23zxeN3+7EA+OwuUTjUCgYEA1QD0tDoQW88SNY5YeF3dSzIWyQ3hvyNVWfBI
2u4P76wPQUW/4mrpiIh4W/7lxB1nmF1ir7NpKXvoY6eAfLxq0b4/pDHTzAEET+ww
XGiPTEncpNE6sDWPYVs4VN6jJ91GBBnGYXavdP/6MdApUGdtYr2CL7Zv/+LIF3Dm
zmDuPpECgYAa40vn419vksfrGix5XVd2nAs0mTCjVyTQtCALYbFS64LB1z+ZaRDo
x+FDfN82RaCOCEbX+YIj/I1To9CdC8wOGjlOYlvDdjQSQLYDpVHFxjj1HOX4gUqT
IzEmisE9iOyMFgrNQITXuozgcJBc+YqdnR6/ckZh+WOjW+/SAGAQWA==
-----END RSA PRIVATE KEY-----"""

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxG24k3W8CDNtgE9alnt2
P6PjNDzpxQ/852KcYF7x1uZj+i6zFT/if7HWA1G9eGpMlpmaA0rC0ca8oj1f+BXm
xsCvB0zb3JBHKeSTIfo++EQYY2cOovSvrbQCqOqWvbh7ZxWibKMUV2gdoEzG2Ne9
jwQh5FH6G3NLVPhjBoOIFG1upnpdEBQa6OrTY5JbVNySh+zkH1+BlLHJIiyRKB7f
7776bTn12hxi5aiL45Ap22LxBoSutkQHmUbtHBcFcn9UGN0aJino3jBWQ7xg+lyv
77hEqMYZ/LWUK88IaodJpJmSiko+skeqgPfkDV5dDM6E8aPtaaBxYdNzpX6X3+hT
8wIDAQAB
-----END PUBLIC KEY-----"""

# =========================
# 🔁 ENCODING PIPELINE
# =========================
def build_encoded_key(key: str) -> str:
    data = key.encode()
    compressed = gzip.compress(data)
    xored = bytes([b ^ XOR_KEY for b in compressed])
    b64 = base64.b64encode(xored)
    return binascii.hexlify(b64).decode()

ENCODED_KEY = build_encoded_key(PUBLIC_KEY)

# =========================
# 🧩 SPLIT INTO FRAGMENTS
# =========================
FRAG_1 = ENCODED_KEY[:len(ENCODED_KEY)//3]
FRAG_2 = ENCODED_KEY[len(ENCODED_KEY)//3: 2*len(ENCODED_KEY)//3]
FRAG_3 = ENCODED_KEY[2*len(ENCODED_KEY)//3:]

# =========================
# 🧪 JWT TOKEN GENERATION
# =========================
def generate_token():
    payload = {
        "user": "harry",
        "role": "cruxbreaker",
        "hint": FRAG_2  # Changed from "fragment_2" to the actual variable
    }
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    # Handling potential byte/string return depending on PyJWT version
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

# =========================
# ⚠️ VULNERABLE VERIFY (intentional CTF vuln)
# =========================
def verify_token(token):
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        if alg == "HS256":
            return jwt.decode(token, PUBLIC_KEY, algorithms=["HS256"])
        else:
            return jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    except jwt.PyJWTError as e:
        print(f"JWT error: {e}")
        return None

# =========================
# 🏠 ROOT ENDPOINT
# =========================
@app.route("/")
def home():
    token = generate_token()
    resp = make_response(jsonify({
        "token": token,
        "note": "The Ministry trusts what tokens claim...
         even those carried by /owl.log ......."
    }))
    resp.headers["X-Ministry-Trace"] = FRAG_1
    return resp

# =========================
# 📁 STATIC FRAGMENT
# =========================
@app.route("/static/owl.log")
def static_frag():
    return f"archive_fragment={FRAG_3}"

# =========================
# 🔍 HINT ENDPOINT
# =========================
@app.route("/hint")
def hint():
    return jsonify({"fragment_2": FRAG_2})

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
