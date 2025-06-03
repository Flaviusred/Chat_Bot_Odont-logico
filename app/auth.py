from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer
from app.models.user import UserModel

SECRET_KEY = "segredo-muito-forte"
COOKIE_NAME = "gestor_session"

templates = Jinja2Templates(directory="app/templates")
auth_router = APIRouter()

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
        raise RedirectResponse("/login", status_code=302)
    return user

@auth_router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@auth_router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if UserModel.autenticar(username, password):
        resp = RedirectResponse("/painel-gestor", status_code=302)
        session = create_session(username)
        resp.set_cookie(COOKIE_NAME, session, httponly=True)
        return resp
    return templates.TemplateResponse("login.html", {"request": request, "error": "Usuário ou senha inválidos"})

@auth_router.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp

@auth_router.get("/cadastrar-admin", response_class=HTMLResponse)
async def cadastrar_admin_form(request: Request):
    return templates.TemplateResponse("cadastrar_admin.html", {"request": request, "ok": None, "erro": None})

@auth_router.post("/cadastrar-admin", response_class=HTMLResponse)
async def cadastrar_admin(request: Request, username: str = Form(...), password: str = Form(...)):
    if UserModel.criar(username, password):
        return templates.TemplateResponse("cadastrar_admin.html", {"request": request, "ok": "Administrador cadastrado com sucesso!", "erro": None})
    else:
        return templates.TemplateResponse("cadastrar_admin.html", {"request": request, "ok": None, "erro": "Usuário já existe!"})