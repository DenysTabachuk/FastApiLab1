from fastapi import FastAPI, Request, HTTPException, Form, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import logging
from datetime import datetime
from bson import ObjectId

from . import schemas
from .database_mongo import get_mongo_db, get_collection
from . import crud_mongo as crud
from .models_mongo import User, Apartment
from . import auth_mongo as auth

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Apartment Rental API (MongoDB)",
    description="API for managing apartment rentals, including user registration, authentication, apartment management, and administration.",
    version="2.0.0",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Templates setup
templates = Jinja2Templates(directory="app/templates")

# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# MongoDB dependency
def get_db():
    """Get MongoDB database instance"""
    return get_mongo_db()

# Auth helpers
def get_current_user_from_cookie(request: Request):
    """Get current user from cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None

    user_email = auth.get_email_from_token(token)
    if not user_email:
        return None

    users_collection = get_collection("users")
    user = users_collection.find_one({"email": user_email})
    if not user:
        return None

    return User.from_db(user)

def get_current_user(request: Request):
    """Get current user (required auth)"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_email = auth.get_email_from_token(token)
    if not user_email:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    users_collection = get_collection("users")
    user = users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return User.from_db(user)

# Routes

@app.get("/")
async def home(request: Request):
    """Home page"""
    current_user = get_current_user_from_cookie(request)
    apartments = crud.get_apartments(current_user=current_user)
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "apartments": apartments,
        "current_user": current_user
    })

@app.get("/register/")
def show_register_page(request: Request):
    """Show registration page"""
    current_user = get_current_user_from_cookie(request)
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
    phone: str = Form(...)):
    """Register a new user"""
    current_user = get_current_user_from_cookie(request)
    
    error = None
    if crud.get_user(email=email):
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

    user_data = schemas.UserCreate(
        email=email, 
        password=password, 
        first_name=first_name, 
        last_name=last_name, 
        phone=phone
    )
    
    crud.create_user(user_data)
    return RedirectResponse(url="/", status_code=302)

@app.get("/login/")
def show_login_page(request: Request):
    """Show login page"""
    current_user = get_current_user_from_cookie(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "current_user": current_user
    })

@app.post("/login/")
def login(
    email: str = Form(...),
    password: str = Form(...),
    request: Request = None):
    """Login user"""
    current_user = get_current_user_from_cookie(request)
    user = crud.get_user(email)
    
    if not user or user["password"] != password:
        error_message = "Невірні облікові дані. Спробуйте ще раз."
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": error_message, 
            "email": email,
            "current_user": current_user
        })

    if not user.get("is_active", True):
        error_message = "Ваш обліковий запис заблоковано. Зверніться до адміністратора."
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": error_message, 
            "email": email,
            "current_user": current_user
        })

    crud.update_user_last_login(user["id"])
    access_token = auth.create_access_token(data={"sub": user["email"]})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="is_logged_in", value="true", httponly=False)
    return response

@app.get("/profile/")
def show_profile_page(request: Request):
    """Show user profile page"""
    current_user = get_current_user(request)
    apartments = crud.get_user_apartments(user_id=current_user["id"])
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "apartments": apartments,
        "current_user": current_user
    })

@app.post("/logout/")
def logout():
    """Logout user"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie('access_token')
    response.delete_cookie('is_logged_in')
    return response

@app.get("/apartments/create")
def get_add_edit_apartment_page(request: Request):
    """Show add apartment page"""
    current_user = get_current_user(request)
    return templates.TemplateResponse("add_edit_apartment.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/apartments/{apartment_id}")
async def show_apartment_page(
    request: Request,
    apartment_id: str
):
    """Show apartment details page"""
    current_user = get_current_user_from_cookie(request)
    
    apartment = crud.get_apartment(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    owner = crud.get_user_by_id(apartment["owner_id"])
    is_owner = current_user is not None and current_user["id"] == apartment["owner_id"]
    
    # Check if apartment is observed by current user
    is_observed = False
    if current_user:
        is_observed = crud.is_apartment_observed(apartment_id, current_user["id"])
    
    return templates.TemplateResponse("apartment.html", {
        "request": request,
        "apartment": apartment,
        "owner": owner,
        "is_owner": is_owner,
        "is_observed": is_observed,
        "current_user": current_user
    })

@app.post("/apartments/")
def create_apartment(
    apartment: schemas.ApartmentCreate,
    request: Request
):
    """Create new apartment"""
    current_user = get_current_user(request)
    apartment = crud.create_apartment(apartment, current_user["id"])
    # Return with id explicitly to avoid 'undefined' errors in the frontend
    return {
        "id": apartment["id"],
        "title": apartment["title"],
        "description": apartment["description"],
        "price": apartment["price"],
        "status": apartment["status"],
        "created_at": apartment["created_at"]
    }

@app.get("/apartments/{apartment_id}/edit/")
def get_edit_apartment_page(
    request: Request,
    apartment_id: str
):
    """Show edit apartment page"""
    current_user = get_current_user(request)
    
    apartment = crud.get_apartment(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    # Check ownership or admin
    if apartment["owner_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to edit this apartment")
    
    return templates.TemplateResponse("add_edit_apartment.html", {
        "request": request,
        "apartment": apartment,
        "current_user": current_user
    })

@app.put("/apartments/{apartment_id}/edit/")
def update_apartment(
    apartment_id: str,
    apartment_data: schemas.ApartmentUpdate,
    request: Request
):
    """Update apartment"""
    current_user = get_current_user(request)
    
    apartment = crud.get_apartment(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    # Check ownership or admin
    if apartment["owner_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to edit this apartment")
    
    updated_apartment = crud.update_apartment(apartment_id, apartment_data)
    return updated_apartment

@app.delete("/apartments/{apartment_id}")
def delete_apartment(
    apartment_id: str,
    request: Request
):
    """Delete apartment"""
    current_user = get_current_user(request)
    
    apartment = crud.get_apartment(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    # Check ownership or admin
    if apartment["owner_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to delete this apartment")
    
    result = crud.delete_apartment(apartment_id)
    if result:
        return {"status": "success"}
    return {"status": "failure"}

# Admin panel functions
def check_admin_access(current_user):
    """Check if user has admin access"""
    if not current_user or not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

@app.get("/admin/")
async def admin_panel(request: Request):
    """Admin panel page"""
    current_user = get_current_user(request)
    check_admin_access(current_user)
    
    # Get system stats
    stats = crud.get_system_stats()
    
    # Get all users
    users = crud.get_all_users()
    
    # Get pending apartments
    pending_apartments = crud.get_pending_apartments()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "stats": stats,
        "users": users,
        "pending_apartments": pending_apartments,
        "current_user": current_user
    })

@app.post("/admin/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: str,
    request: Request
):
    """Toggle user active status"""
    current_user = get_current_user(request)
    check_admin_access(current_user)
    
    user = crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cannot deactivate yourself
    if user["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot change your own status")
    
    # Toggle status
    is_active = not user.get("is_active", True)
    updated_user = crud.update_user_status(user_id, is_active)
    
    return updated_user

@app.post("/admin/apartments/{apartment_id}/moderate")
def moderate_apartment(
    apartment_id: str,
    status: str = Form(...),
    request: Request = None
):
    """Moderate apartment"""
    current_user = get_current_user(request)
    check_admin_access(current_user)
    
    apartment = crud.get_apartment(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    updated_apartment = crud.moderate_apartment(apartment_id, status, current_user["id"])
    
    return updated_apartment

# New MongoDB-specific features

@app.get("/api/apartments/search")
def search_apartments(
    query: str = None,
    min_price: float = None,
    max_price: float = None,
    city: str = None,
    sort_by: str = None,
    request: Request = None
):
    """
    Search apartments with advanced MongoDB features
    
    This is a new feature enabled by MongoDB's powerful query capabilities
    """
    current_user = get_current_user_from_cookie(request)
    
    # Build query
    filter_query = {}
    
    # Show only approved apartments for non-admins
    if not current_user or not current_user.get("is_admin", False):
        filter_query["status"] = "approved"
    
    # Text search
    if query:
        filter_query["$text"] = {"$search": query}
    
    # Price range
    price_query = {}
    if min_price is not None:
        price_query["$gte"] = min_price
    if max_price is not None:
        price_query["$lte"] = max_price
    if price_query:
        filter_query["price"] = price_query
    
    # City filter
    if city:
        filter_query["location.city"] = {"$regex": city, "$options": "i"}
    
    # Get collection
    apartments_collection = get_collection("apartments")
    
    # Build sort
    sort_options = {}
    if sort_by == "price_asc":
        sort_options["price"] = 1
    elif sort_by == "price_desc":
        sort_options["price"] = -1
    elif sort_by == "newest":
        sort_options["created_at"] = -1
    elif sort_by == "oldest":
        sort_options["created_at"] = 1
    
    # Execute query
    cursor = apartments_collection.find(filter_query)
    
    # Apply sort if specified
    if sort_options:
        cursor = cursor.sort(list(sort_options.items()))
    
    # Convert to list and process
    apartments = [Apartment.from_db(apartment) for apartment in list(cursor)]
    
    return apartments

@app.get("/api/stats/city-distribution")
def get_city_stats(request: Request):
    """
    Get apartment distribution by city
    
    This is a new feature enabled by MongoDB's aggregation framework
    """
    current_user = get_current_user(request)
    check_admin_access(current_user)
    
    apartments_collection = get_collection("apartments")
    
    # Aggregation pipeline to get apartments by city
    pipeline = [
        {"$match": {"status": "approved"}},
        {"$group": {
            "_id": "$location.city",
            "count": {"$sum": 1},
            "avg_price": {"$avg": "$price"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = list(apartments_collection.aggregate(pipeline))
    
    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            "city": result["_id"],
            "count": result["count"],
            "avg_price": round(result["avg_price"], 2)
        })
    
    return formatted_results

# Apartment observation routes
@app.post("/apartments/{apartment_id}/observe")
def observe_apartment_endpoint(
    apartment_id: str,
    request: Request
):
    """Add apartment to user's observation list"""
    current_user = get_current_user(request)
    
    observation = crud.observe_apartment(apartment_id, current_user["id"])
    if not observation:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    return {"status": "success", "observed": True}

@app.delete("/apartments/{apartment_id}/observe")
def remove_observation_endpoint(
    apartment_id: str,
    request: Request
):
    """Remove apartment from user's observation list"""
    current_user = get_current_user(request)
    
    result = crud.remove_observation(apartment_id, current_user["id"])
    return {"status": "success", "observed": False}

@app.get("/profile/observations")
def show_observations_page(request: Request):
    """Show user's observed apartments page"""
    current_user = get_current_user(request)
    
    observed_apartments = crud.get_user_observations(current_user["id"])
    
    return templates.TemplateResponse("observations.html", {
        "request": request,
        "apartments": observed_apartments,
        "current_user": current_user
    })

# Exception handlers

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    current_user = get_current_user_from_cookie(request)
    
    # If unauthorized, redirect to login
    if exc.status_code == 401:
        return RedirectResponse(url="/login/", status_code=302)
    
    return templates.TemplateResponse("error.html", {
        "request": request,
        "status_code": exc.status_code,
        "detail": exc.detail,
        "current_user": current_user
    })

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    current_user = get_current_user_from_cookie(request)
    
    return templates.TemplateResponse("error.html", {
        "request": request,
        "status_code": 422,
        "detail": str(exc),
        "current_user": current_user
    }) 