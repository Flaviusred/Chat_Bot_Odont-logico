from app.models.user import UserModel
from itsdangerous import URLSafeSerializer
from fastapi import Request, HTTPException

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
        if user:
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
    return UserModel.autenticar(username, password)