from fastapi import FastAPI
from app.routes import users, courses

app = FastAPI()

app.include_router(users.router)
app.include_router(courses.router)

@app.get('/')
async def root():
    return {'message': 'Welcome to Lumber LMS'}

