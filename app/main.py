from fastapi import FastAPI, Depends, Request, HTTPException, Form, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
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
logging.basicConfig(level=logging.INFO)  # Налаштовуємо базову конфігурацію
logger = logging.getLogger(__name__)  # Створюємо логер для цього модуля

app = FastAPI()

# Налаштування Jinja2 для шаблонів
templates = Jinja2Templates(directory="app/templates")

# Підключення статичних файлів (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def home_page(
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

    error = None
    if crud.get_user(db, email=email):
        error = "Користувач із таким email вже існує"
    elif password != confirm_password:
        error = "Паролі не співпадають"

    if error:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": error,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone
        })

    crud.create_user(db, schemas.UserCreate(
        email=email, 
        password=password, 
        first_name=first_name, 
        last_name=last_name, 
        phone=phone
    ))

    return RedirectResponse(url="/", status_code=302)

@app.get("/login/")
def show_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login/")
def login( email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
        request: Request = None 
    ):
    
    user = crud.get_user(db, email)
    
    if not user or not user.password == password:
        error_message = "Невірні облікові дані. Спробуйте ще раз."
        return templates.TemplateResponse("login.html", {"request": request, "error": error_message, "email": email,})

    access_token = auth.create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=302)  
    response.set_cookie(key="access_token", value=access_token, httponly=True) 
    response.set_cookie(key="is_logged_in", value="true", httponly=False) 
    return response

@app.get("/profile/")
def show_profile_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(auth.get_current_user)  
    ):
    
    apartments = crud.get_user_apartments(db, user_id=current_user.id)  

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

@app.get("/apartments/create")
def get_add_edit_apartment_page(request: Request, current_user: models.User = Depends(auth.get_current_user)  ):
    return templates.TemplateResponse("add_edit_apartment.html", {"request": request})

@app.get("/apartments/{apartment_id}")
def show_apartment_page(request: Request, 
                        apartment_id: int, 
                        db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user_from_cookie)
                        ):
    apartment = crud.get_apartment(db, apartment_id)

    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")

    owner = crud.get_user_by_id(db, apartment.owner_id)

    is_owner = current_user is not None and current_user.id == apartment.owner_id

    return templates.TemplateResponse("apartment.html", {
        "request": request,
        "apartment": apartment,
        "owner": owner,
        "is_owner": is_owner  
    })

@app.post("/apartments/")
def create_apartment(
    apartment: schemas.ApartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
): 
    new_apartment = crud.create_apartment(db, apartment, current_user.id)
    return {"redirect_url": f"/apartments/{new_apartment.id}"}

@app.get("/apartments/{apartment_id}/edit/")
def get_edit_apartment_page(
      request: Request,
      apartment_id: int ,
      db: Session = Depends(get_db),
      current_user: models.User = Depends(auth.get_current_user)
    ):

    apartment = crud.get_apartment(db, apartment_id)

    if apartment is None:
        raise HTTPException(status_code=404, detail="Apartment not found")

    if apartment.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to edit this apartment.")

    return templates.TemplateResponse("add_edit_apartment.html", {
         "request": request,
        "apartment": apartment,
    })

@app.put("/apartments/{apartment_id}/edit/")
def update_apartment(
    apartment_id: int,
    apartment_data: schemas.ApartmentUpdate,  
    db: Session = Depends(get_db)
):
    if not crud.get_apartment(db, apartment_id):
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    crud.update_apartment(db, apartment_id, apartment_data)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
        "message": "Apartment updated successfully",
        "redirect_url": f"/apartments/{apartment_id}" 
        }
    )
    
@app.delete("/apartments/{apartment_id}")
def delete_apartment(
        apartment_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(auth.get_current_user)
    ):
    apartment = crud.get_apartment(db, apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")

    if apartment.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this apartment.")

    crud.delete_apartment(db, apartment_id)


    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Apartment deleted successfully", "apartment_id": apartment_id}
    )





@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")  
    elif exc.status_code == 403:
        return templates.TemplateResponse("error.html", {"request": request, "title" : "Доступ заборонено", "message": "У вас немає прав доступу до цієї сторінки"})
    elif exc.status_code == 404:
        return templates.TemplateResponse("error.html", {"request": request, "title": "Сторінку не знайдено", "message": "Сторінку не знайдено"})

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    errors = exc.errors()

    error_messages = [{"field": e['loc'][-1], "message": e['msg']} for e in errors]
    return JSONResponse(
        status_code=400,
        content={"detail": error_messages}
    )
