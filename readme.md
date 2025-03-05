# Створення віртуального середовища
python -m venv venv

# Активація віртуального середовища
venv\Scripts\activate

# Встановлення залежностей з requirements.txt
pip install -r requirements.txt

# Запуск сервера
uvicorn main:app --reload

# Сервер буде доступний за адресою:
# http://127.0.0.1:8000
