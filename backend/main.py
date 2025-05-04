import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict
from routers import accounts
from routers import auth
from routers import ingredients
from routers import products
from routers import recipes
from routers import materials
from routers import merchandise

app = FastAPI()
origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router, prefix='/accounts', tags=['accounts'])
app.include_router(auth.router)
app.include_router(ingredients.router, prefix='/ingredients', tags=['ingredients'])
app.include_router(products.router, prefix='/products', tags=['products'])
app.include_router(recipes.router, prefix='/recipes', tags=['recipes'])
app.include_router(materials.router, prefix='/materials', tags=['materials'])
app.include_router(merchandise.router, prefix='/merchandise', tags=['merchandise'])

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="127.0.0.1", reload=True)