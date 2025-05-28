from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api_routes import router as api_router
from app.gestor_routes import gestor_router

app = FastAPI()

app.include_router(api_router)
app.include_router(gestor_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")