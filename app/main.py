from datetime import timedelta
from fastapi import FastAPI, Depends, Request, HTTPException, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from . import  models, schemas, crud, auth
from .database import get_db
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import HTTPException, Form, Depends
from sqlalchemy.orm import Session

import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger('uvicorn.error')


app = FastAPI()

# Налаштування Jinja2 для шаблонів
templates = Jinja2Templates(directory="app/templates")

# Підключення статичних файлів (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root(
        request: Request,
        db: Session = Depends(get_db)):

    apartments = crud.get_all_apartments(db)

    return templates.TemplateResponse("home.html", {
        "request": request,
        "apartments": apartments,
    })

@app.get("/register/")
def show_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register/")
def register_user(
    request: Request,  
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...), 
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(get_db)):

    existing_user = crud.get_user(db, email=email)
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "User with this email already exists"})
    
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Паролі не співпадають"})
    
    user_data = schemas.UserCreate(
        email=email, 
        password=password, 
        first_name=first_name, 
        last_name=last_name, 
        phone=phone
    )
    
    crud.create_user(db, user_data)
    return RedirectResponse(url="/", status_code=302)

@app.get("/login/")
def show_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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
    response.set_cookie(key="is_logged_in", value="true", httponly=False) 
    return response

@app.get("/profile/")
def show_profile_page(
        request: Request,
        db: Session = Depends(get_db)):
    
    token = request.cookies.get("access_token")
    current_user = None  

    if token:
        try:
            current_user = auth.get_current_user(token, db)
        except HTTPException:
            current_user = None

    if current_user:
        apartments = crud.get_user_apartments(db, user_id=current_user.id)  
    else:
        apartments = []

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "apartments": apartments
    })

@app.post("/logout/")
def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie('access_token')
    response.delete_cookie('is_logged_in')  

    return response

@app.get("/apartments/")
def add_apartment_page(request: Request):
    return templates.TemplateResponse("add_edit_apartment.html", {"request": request})

@app.get("/apartments/{apartment_id}")
def show_apartment_page(request: Request, apartment_id: int, db: Session = Depends(get_db)):
    apartment = crud.get_apartment(db, apartment_id)
    owner = crud.get_user_by_id(db, apartment.owner_id)

    token = request.cookies.get("access_token")
    is_owner = False
    if token:
            try:
                current_user = auth.get_current_user(token, db)
                if current_user.id == apartment.owner_id:
                    is_owner = True
            except HTTPException:
                current_user = None

    return templates.TemplateResponse("apartment.html", {
        "request": request,
        "apartment": apartment,
        "owner": owner,
        "is_owner": is_owner  
    })

@app.post("/apartments/")
def create_apartment(
    title: str = Form(...), 
    description: str = Form(...), 
    price: float = Form(...),
    location: str = Form(...),
    db: Session = Depends(get_db),
): 
    apartment_create = schemas.ApartmentCreate(
        title=title, 
        description=description, 
        price=price, 
        location=location, 
        owner_id=1) 
    crud.create_apartment(db, apartment_create)
    response = RedirectResponse(url="/", status_code=302)  
    return response

@app.get("/apartments/{apartment_id}/edit/")
def get_edit_apartment_page(
      request: Request,
      apartment_id: int ,
      db: Session = Depends(get_db),
    ):

    apartment = crud.get_apartment(db, apartment_id)
    return templates.TemplateResponse("add_edit_apartment.html", {
         "request": request,
        "apartment": apartment,
    })

@app.post("/apartments/{apartment_id}/edit/")
def get_edit_apartment_page(
        apartment_id: int,
        title: str = Form(...), 
        description: str = Form(...), 
        price: float = Form(...),
        location: str = Form(...),
        db: Session = Depends(get_db),
    ):

    apartment = schemas.ApartmentUpdate(
        title=title, 
        description=description, 
        price=price, 
        location=location)
    
    crud.update_apartment(db, apartment_id, apartment)
    return RedirectResponse(url=f"/apartments/{apartment_id}", status_code=302)

@app.delete("/apartments/{apartment_id}")
def delete_apartment(
        apartment_id: int,
        db: Session = Depends(get_db),
    ):

    apartment = crud.get_apartment(db, apartment_id)
    if apartment is None:
        raise HTTPException(status_code=404, detail="Apartment not found")

    crud.delete_apartment(db, apartment_id)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Apartment deleted successfully", "apartment_id": apartment_id}
    )
