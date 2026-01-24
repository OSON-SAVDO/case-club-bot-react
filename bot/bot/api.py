from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Сохтани барномаи FastAPI
app = FastAPI(title="Case Club API")

# Танзимоти CORS (барои он ки React тавонад ба ин API пайваст шавад)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Дар лоиҳаи воқеӣ ин ҷо адреси сайти React-ро менависем
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели маълумот барои корбар
class User(BaseModel):
    id: int
    name: str
    phone: str
    status: str

# Маълумоти намунавӣ (ин ҷо дар оянда аз базаи SQLite маълумот меояд)
users_db = [
    {"id": 1, "name": "Алишер", "phone": "+992900000000", "status": "Активен"},
    {"id": 2, "name": "Мадина", "phone": "+992911111111", "status": "Новый"},
    {"id": 3, "name": "Искандар", "phone": "+992922222222", "status": "Активен"}
]

@app.get("/")
async def root():
    return {"message": "API для Кейс-клуба работает!"}

# Гирифтани рӯйхати ҳамаи корбарон барои Админка
@app.get("/api/users", response_model=List[User])
async def get_users():
    return users_db

# Гирифтани омори умумӣ барои Dashboard
@app.get("/api/stats")
async def get_stats():
    return {
        "total_users": len(users_db),
        "active_cases": 5,
        "new_messages": 12
    }

# Фармон барои ба кор даровардани API (дар терминал):
# uvicorn api:app --reload
