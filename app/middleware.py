from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from . import auth, models
from .database import SessionLocal

class CurrentUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Отримуємо доступ до шаблонів
        if hasattr(request.app, 'templates'):
            templates = request.app.templates
            
            # Отримуємо поточного користувача
            db = SessionLocal()
            try:
                current_user = await auth.get_current_user_from_cookie(request, db)
            except:
                current_user = None
            finally:
                db.close()
            
            # Додаємо current_user до глобального контексту шаблонів
            templates.env.globals['current_user'] = current_user
        
        response = await call_next(request)
        return response 