## Створення віртуального середовища
python -m venv venv

## Активація віртуального середовища
venv\Scripts\activate

## Встановлення залежностей з requirements.txt
pip install -r requirements.txt

## Встановлення БД
docker-compose up -d

## Запуск сервера
uvicorn app.main:app --reload

## Сервер буде доступний за адресою:
## http://127.0.0.1:8000
