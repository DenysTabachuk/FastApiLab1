from fastapi import FastAPI, Depends, Request, HTTPException, Form, status, Query
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
from .middleware import CurrentUserMiddleware
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
from .pg_repo import PgRepository


# Налаштування логування
logging.basicConfig(level=logging.INFO)  # Налаштовуємо базову конфігурацію
logger = logging.getLogger(__name__)  # Створюємо логер для цього модуля

from fastapi import FastAPI

app = FastAPI(
    title="Apartment Rental API",
    description="API for managing apartment rentals, including user registration, authentication, apartment management, and administration.",
    version="1.0.0",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Додаємо middleware
app.add_middleware(CurrentUserMiddleware)

# Налаштування Jinja2 для шаблонів
templates = Jinja2Templates(directory="app/templates")

# Підключення статичних файлів (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def home(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user_from_cookie)
):
    apartments = crud.get_apartments(db, current_user=current_user)
    return templates.TemplateResponse("home.html", {
        "request": request,
        "apartments": apartments,
        "current_user": current_user
    })

@app.get("/register/")
def show_register_page(request: Request, current_user: models.User = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "current_user": current_user
    })

@app.post("/register/")
def register_user(
    request: Request,  
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...), 
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user_from_cookie)):

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
            "phone": phone,
            "current_user": current_user
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
def show_login_page(request: Request, current_user: models.User = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "current_user": current_user
    })

@app.post("/login/")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    request: Request = None,
    current_user: models.User = Depends(auth.get_current_user_from_cookie)
):
    user = crud.get_user(db, email)
    
    if not user or not user.password == password:
        error_message = "Невірні облікові дані. Спробуйте ще раз."
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": error_message, 
            "email": email,
            "current_user": current_user
        })

    if not user.is_active:
        error_message = "Ваш обліковий запис заблоковано. Зверніться до адміністратора."
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": error_message, 
            "email": email,
            "current_user": current_user
        })

    crud.update_user_last_login(db, user.id)
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
        "apartments": apartments,
        "current_user": current_user
    })

@app.post("/logout/")
def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie('access_token')
    response.delete_cookie('is_logged_in')  

    return response

@app.get("/apartments/create")
def get_add_edit_apartment_page(
    request: Request, 
    current_user: models.User = Depends(auth.get_current_user)
):
    return templates.TemplateResponse("add_edit_apartment.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/apartments/{apartment_id}")
async def show_apartment_page(request: Request, 
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
        "is_owner": is_owner,
        "current_user": current_user
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
      apartment_id: int,
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
        "current_user": current_user
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

def check_admin_access(current_user: models.User):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied. Admin privileges required.")

@app.get("/admin/")
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    check_admin_access(current_user)  

    # оце може краще в crud винести
    stats = {
        "total_users": db.query(models.User).count(),
        "active_users": db.query(models.User).filter(models.User.is_active == True).count(),
        "total_apartments": db.query(models.Apartment).count(),
        "pending_apartments": db.query(models.Apartment).filter(models.Apartment.status == "pending").count(),
        "approved_apartments": db.query(models.Apartment).filter(models.Apartment.status == "approved").count(),
        "rejected_apartments": db.query(models.Apartment).filter(models.Apartment.status == "rejected").count(),
        "average_price": db.query(func.avg(models.Apartment.price)).scalar() or 0,
        "total_owners": db.query(models.User).filter(models.User.owned_apartments.any()).count()
    }

    users = db.query(models.User).all()

    # Отримуємо квартири, що очікують модерації
    pending_apartments = db.query(models.Apartment).filter(models.Apartment.status == "pending").all()

    return templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "users": users,
        "pending_apartments": pending_apartments,
        "stats": stats,
        "current_user": current_user  
    })

@app.post("/admin/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    check_admin_access(current_user)
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot block or unblock your own account"
        )
    
    crud.update_user_status(db, user_id, not user.is_active)
    return RedirectResponse(url="/admin/", status_code=302)

@app.post("/admin/apartments/{apartment_id}/moderate")
def moderate_apartment(
    apartment_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    check_admin_access(current_user)
    
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    crud.moderate_apartment(db, apartment_id, status, current_user.id)
    return RedirectResponse(url="/admin/", status_code=302)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException, current_user: models.User = Depends(auth.get_current_user_from_cookie)):
    # Якщо помилка 401 (не авторизований), перенаправити на сторінку логіну
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    
    # Якщо помилка 403 (доступ заборонено), показати сторінку помилки з відповідним повідомленням
    elif exc.status_code == 403:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Доступ заборонено", 
            "message": "У вас немає прав доступу до цієї сторінки",
            "current_user": current_user 
        })
    
    # Якщо помилка 404 (не знайдено), показати сторінку помилки з повідомленням
    elif exc.status_code == 404:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Сторінку не знайдено", 
            "message": "Сторінку не знайдено",
            "current_user": current_user  
        })
    
    # Якщо інша помилка, просто відобразити її в JSON відповіді
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError, current_user: models.User = Depends(auth.get_current_user_from_cookie)):
    errors = exc.errors()
    error_messages = [{"field": e['loc'][-1], "message": e['msg']} for e in errors]

    # Повертаємо шаблон з помилками та поточним користувачем
    return JSONResponse(
        status_code=400,
        content={"detail": error_messages, "current_user": current_user}  
    )

# New PostgreSQL-specific endpoints

@app.get("/api/apartments/search")
async def search_apartments(
    query: str = "",
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    city: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: models.User = Depends(auth.get_current_user_from_cookie)
):
    """
    Search apartments using PostgreSQL full-text search capabilities.
    """
    results = PgRepository.search_apartments(
        query=query,
        min_price=min_price,
        max_price=max_price,
        city=city,
        limit=limit,
        offset=offset
    )
    
    return {"results": results, "count": len(results)}

@app.get("/api/apartments/nearby")
async def find_nearby_apartments(
    lat: float,
    lon: float,
    radius_km: float = Query(5, ge=0.1, le=50),
    current_user: models.User = Depends(auth.get_current_user_from_cookie)
):
    """
    Find apartments near a specific location using PostgreSQL geospatial capabilities.
    """
    results = PgRepository.get_nearby_apartments(lat, lon, radius_km)
    return {"results": results, "count": len(results)}

@app.post("/api/apartments/{apartment_id}/features")
async def update_apartment_features(
    apartment_id: int,
    features: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update apartment features using PostgreSQL JSONB operations.
    """
    # Check if user owns the apartment
    apartment = crud.get_apartment(db, apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    if apartment.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this apartment")
    
    success = PgRepository.update_apartment_features(apartment_id, features)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update apartment features")
    
    return {"message": "Features updated successfully"}

@app.get("/api/apartments/filter-by-features")
async def filter_apartments_by_features(
    features: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user_from_cookie)
):
    """
    Find apartments with specific features using PostgreSQL JSONB querying.
    """
    results = PgRepository.get_apartments_with_jsonb_features(features)
    return {"results": results, "count": len(results)}

@app.post("/api/locations/{location_id}/coordinates")
async def set_location_coordinates(
    location_id: int,
    lat: float,
    lon: float,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update location coordinates using PostgreSQL JSONB.
    """
    # Check if user is admin or owns apartments at this location
    if not current_user.is_admin:
        # Check if user has apartments at this location
        user_has_apartment = db.query(models.Apartment).filter(
            models.Apartment.owner_id == current_user.id,
            models.Apartment.location_id == location_id
        ).first()
        
        if not user_has_apartment:
            raise HTTPException(status_code=403, detail="Not authorized to update this location")
    
    success = PgRepository.set_location_coordinates(location_id, lat, lon)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update location coordinates")
    
    return {"message": "Coordinates updated successfully"}

@app.get("/api/stats/apartments")
async def get_apartment_statistics(
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get advanced statistics about apartments using PostgreSQL aggregations.
    Admin access required.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = PgRepository.get_apartment_statistics()
    return stats

@app.get("/api/stats/user-activity")
async def get_user_activity_statistics(
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get statistics about user activity using PostgreSQL window functions.
    Admin access required.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = PgRepository.get_user_activity_statistics()
    return stats

# Add a new admin page to show advanced statistics
@app.get("/admin/statistics/")
async def admin_statistics_page(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user)
):
    check_admin_access(current_user)  
    
    apartment_stats = PgRepository.get_apartment_statistics()
    user_stats = PgRepository.get_user_activity_statistics()
    
    return templates.TemplateResponse("admin_statistics.html", {
        "request": request,
        "apartment_stats": apartment_stats,
        "user_stats": user_stats,
        "current_user": current_user  
    })
