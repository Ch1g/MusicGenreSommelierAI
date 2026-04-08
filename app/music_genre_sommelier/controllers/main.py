from fastapi import FastAPI
from music_genre_sommelier.controllers import auth

app = FastAPI()

app.include_router(auth.router)

@app.get("/")
def root():
    return {"Hello": "World"}
