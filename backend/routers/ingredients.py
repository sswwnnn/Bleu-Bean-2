from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date
from database import get_db_connection  
from models import IngredientCreate, IngredientUpdate, IngredientOut

router = APIRouter(
    prefix="/ingredients",
    tags=["ingredients"]
)

@router.get("/")
async def get_ingredients():
    return{"message": "here are your ingredients"}

# threshold for stock status
thresholds = {
    "g": 50,
    "kg": 0.5,
    "ml": 100,
    "l": 0.5,
    "pcs": 5
}

def get_status(amount: float, measurement: str):  
    if amount <= 0:
        return "Not Available"
    elif amount <= thresholds.get(measurement, 1):
        return "Low on Stock"
    return "Available"

#create
@router.post("/ingredients/", response_model=IngredientOut)
async def add_ingredient(ingredient: IngredientCreate):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        status = get_status(ingredient.Amount, ingredient.Measurement)
        await cursor.execute("""
            INSERT INTO Ingredients (IngredientName, Amount, Measurement, BestBeforeDate, ExpirationDate, Status)
            OUTPUT INSERTED.*
            VALUES (?, ?, ?, ?, ?, ?)
        """, ingredient.IngredientName, ingredient.Amount, ingredient.Measurement,
             ingredient.BestBeforeDate, ingredient.ExpirationDate, status)
        row = await cursor.fetchone()
        return {
            "IngredientID": row.IngredientID,
            "IngredientName": row.IngredientName,
            "Amount": row.Amount,
            "Measurement": row.Measurement,
            "BestBeforeDate": row.BestBeforeDate,
            "ExpirationDate": row.ExpirationDate,
            "Status": row.Status
        }

#get all ingredients
@router.get("/ingredients/", response_model=List[IngredientOut])
async def get_all_ingredients():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Ingredients")
        rows = await cursor.fetchall()
        return [
            {
                "IngredientID": row.IngredientID,
                "IngredientName": row.IngredientName,
                "Amount": row.Amount,
                "Measurement": row.Measurement,
                "BestBeforeDate": row.BestBeforeDate,
                "ExpirationDate": row.ExpirationDate,
                "Status": row.Status
            }
            for row in rows
        ]

#update ingredients
@router.put("/ingredients/{ingredient_id}", response_model=IngredientOut)
async def update_ingredient(ingredient_id: int, ingredient: IngredientUpdate):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        status = get_status(ingredient.Amount, ingredient.Measurement)
        await cursor.execute("""
            UPDATE Ingredients
            SET IngredientName = ?, Amount = ?, Measurement = ?, BestBeforeDate = ?, ExpirationDate = ?, Status = ?
            WHERE IngredientID = ?
        """, ingredient.IngredientName, ingredient.Amount, ingredient.Measurement,
             ingredient.BestBeforeDate, ingredient.ExpirationDate, status, ingredient_id)

        await cursor.execute("SELECT * FROM Ingredients WHERE IngredientID = ?", ingredient_id)
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ingredient not found")

        return {
            "IngredientID": row.IngredientID,
            "IngredientName": row.IngredientName,
            "Amount": row.Amount,
            "Measurement": row.Measurement,
            "BestBeforeDate": row.BestBeforeDate,
            "ExpirationDate": row.ExpirationDate,
            "Status": row.Status
        }

#delete ingredients
@router.delete("/ingredients/{ingredient_id}")
async def delete_ingredient(ingredient_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM Ingredients WHERE IngredientID = ?", ingredient_id)
    return {"message": "Ingredient deleted successfully"}
