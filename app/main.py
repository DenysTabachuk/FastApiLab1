from datetime import timedelta
from fastapi import FastAPI, Depends, Request, HTTPException, Form, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from . import  models, schemas, crud, auth
from .database import SessionLocal, engine
from .config import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)  # або DEBUG для більш детальних логів
logger = logging.getLogger('uvicorn.error')


app = FastAPI()

# Налаштування Jinja2 для шаблонів
templates = Jinja2Templates(directory="app/templates")

# Підключення статичних файлів (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register/")
def show_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register/")
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)):

   user_data = schemas.UserCreate(username=username, email=email, password=password)
   new_user = crud.create_user(db, user_data)

   return templates.TemplateResponse("register.html", {"request": request, "message": "Успішна реєстрація!"})


@app.get("/login/")
def show_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import HTTPException, Form, Depends
from sqlalchemy.orm import Session

@app.post("/login/")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, email)
    if not user or not user.password == password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    
    response = RedirectResponse(url="/", status_code=302)  
    response.set_cookie(key="access_token", value=access_token, httponly=True) 

    return response
