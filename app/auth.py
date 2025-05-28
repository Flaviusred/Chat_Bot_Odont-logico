from fastapi import Request, HTTPException
from passlib.hash import bcrypt
from itsdangerous import URLSafeSerializer

USERS = {
    "admin": bcrypt.hash("admin123")
}

SECRET_KEY = "segredo-muito-forte"
COOKIE_NAME = "gestor_session"

def create_session(username):
    s = URLSafeSerializer(SECRET_KEY)
    return s.dumps({"user": username})

def get_current_user(request: Request):
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return None
    s = URLSafeSerializer(SECRET_KEY)
    try:
        data = s.loads(cookie)
        user = data.get("user")
        if user in USERS:
            return user
    except Exception:
        return None
    return None

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user

def try_login(username, password):
    hash_ = USERS.get(username)
    return hash_ and bcrypt.verify(password, hash_)