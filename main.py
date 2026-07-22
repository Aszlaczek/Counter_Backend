from fastapi import FastAPI
from .Models import models

app = FastAPI()

@app.get("/")
def home():
    return {"message" :"Hello World"}