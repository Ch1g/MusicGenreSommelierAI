from fastapi import FastAPI
from music_genre_sommelier.controllers import audio, auth, inference, transactions

app = FastAPI()

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(audio.router)
app.include_router(inference.router)


@app.get("/")
def root():
    return {"Hello": "World"}
