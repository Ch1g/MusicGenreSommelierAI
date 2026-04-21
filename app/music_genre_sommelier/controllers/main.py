import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from music_genre_sommelier.controllers import audio, auth, inference, ml_models, transactions
from music_genre_sommelier.utils.errors.errors import AppError

app = FastAPI()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.exception(str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(audio.router)
app.include_router(inference.router)
app.include_router(ml_models.router)


@app.get("/api")
def root():
    return {"Hello": "World"}
