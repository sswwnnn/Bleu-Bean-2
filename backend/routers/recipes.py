from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from database import get_db_connection

router = APIRouter(
    prefix="/recipes",
    tags=["recipes"]
)

# models
class IngredientInRecipe(BaseModel):
    IngredientID: int
    Amount: float
    Measurement: str

class MaterialInRecipe(BaseModel):
    MaterialID: int
    Quantity: float
    Measurement: str

class RecipeCreate(BaseModel):
    ProductID: int
    RecipeName: str
    Ingredients: List[IngredientInRecipe]
    Materials: List[MaterialInRecipe]

class RecipeUpdate(RecipeCreate):
    pass

# get all recipes
@router.get("/")
async def get_all_recipes():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Recipes")
        recipes = await cursor.fetchall()

        recipe_list = []
        for recipe in recipes:
            recipe_id = recipe.RecipeID

            await cursor.execute("""
                SELECT ri.RecipeIngredientID, ri.Amount, i.IngredientName, i.Measurement
                FROM RecipeIngredients ri
                JOIN Ingredients i ON ri.IngredientID = i.IngredientID
                WHERE ri.RecipeID = ?
            """, (recipe_id,))
            ingredients = await cursor.fetchall()

            await cursor.execute("""
                SELECT rm.RecipeMaterialID, rm.Quantity, m.MaterialName, m.MaterialMeasurement
                FROM RecipeMaterials rm
                JOIN Materials m ON rm.MaterialID = m.MaterialID
                WHERE rm.RecipeID = ?
            """, (recipe_id,))
            materials = await cursor.fetchall()

            recipe_list.append({
                "RecipeID": recipe.RecipeID,
                "ProductID": recipe.ProductID,
                "RecipeName": recipe.RecipeName,
                "Ingredients": [
                    {
                        "RecipeIngredientID": row.RecipeIngredientID,
                        "IngredientName": row.IngredientName,
                        "Amount": row.Amount,
                        "Measurement": row.Measurement
                    } for row in ingredients
                ],
                "Materials": [
                    {
                        "RecipeMaterialID": row.RecipeMaterialID,
                        "MaterialName": row.MaterialName,
                        "Quantity": row.Quantity,
                        "Measurement": row.MaterialMeasurement
                    } for row in materials
                ]
            })

        return recipe_list

# get recipe details
@router.get("/{recipe_id}")
async def get_recipe_details(recipe_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Recipes WHERE RecipeID = ?", (recipe_id,))
        recipe = await cursor.fetchone()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        await cursor.execute("""
            SELECT ri.RecipeIngredientID, ri.Amount, i.IngredientName, i.Measurement
            FROM RecipeIngredients ri
            JOIN Ingredients i ON ri.IngredientID = i.IngredientID
            WHERE ri.RecipeID = ?
        """, (recipe_id,))
        ingredients = await cursor.fetchall()

        await cursor.execute("""
            SELECT rm.RecipeMaterialID, rm.Quantity, m.MaterialName, m.MaterialMeasurement
            FROM RecipeMaterials rm
            JOIN Materials m ON rm.MaterialID = m.MaterialID
            WHERE rm.RecipeID = ?
        """, (recipe_id,))
        materials = await cursor.fetchall()

        return {
            "RecipeID": recipe.RecipeID,
            "ProductID": recipe.ProductID,
            "RecipeName": recipe.RecipeName,
            "Ingredients": [
                {
                    "RecipeIngredientID": row.RecipeIngredientID,
                    "IngredientName": row.IngredientName,
                    "Amount": row.Amount,
                    "Measurement": row.Measurement
                } for row in ingredients
            ],
            "Materials": [
                {
                    "RecipeMaterialID": row.RecipeMaterialID,
                    "MaterialName": row.MaterialName,
                    "Quantity": row.Quantity,
                    "Measurement": row.MaterialMeasurement
                } for row in materials
            ]
        }

# create recipes
@router.post("/")
async def create_recipe(recipe: RecipeCreate):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            INSERT INTO Recipes (ProductID, RecipeName)
            OUTPUT INSERTED.RecipeID
            VALUES (?, ?)
        """, recipe.ProductID, recipe.RecipeName)
        new_recipe_id = (await cursor.fetchone()).RecipeID

        for ing in recipe.Ingredients:
            await cursor.execute("""
                INSERT INTO RecipeIngredients (RecipeID, IngredientID, Amount, Measurement)
                VALUES (?, ?, ?, ?)
            """, new_recipe_id, ing.IngredientID, ing.Amount, ing.Measurement)

        for mat in recipe.Materials:
            await cursor.execute("""
                INSERT INTO RecipeMaterials (RecipeID, MaterialID, Quantity, Measurement)
                VALUES (?, ?, ?, ?)
            """, new_recipe_id, mat.MaterialID, mat.Quantity, mat.Measurement)

    return {"message": "Recipe created successfully", "RecipeID": new_recipe_id}

# update recipes
@router.put("/{recipe_id}")
async def update_recipe(recipe_id: int, recipe: RecipeUpdate):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE Recipes SET ProductID = ?, RecipeName = ? WHERE RecipeID = ?",
                             recipe.ProductID, recipe.RecipeName, recipe_id)

        await cursor.execute("DELETE FROM RecipeIngredients WHERE RecipeID = ?", (recipe_id,))
        for ing in recipe.Ingredients:
            await cursor.execute("""
                INSERT INTO RecipeIngredients (RecipeID, IngredientID, Amount, Measurement)
                VALUES (?, ?, ?, ?)
            """, recipe_id, ing.IngredientID, ing.Amount, ing.Measurement)

        await cursor.execute("DELETE FROM RecipeMaterials WHERE RecipeID = ?", (recipe_id,))
        for mat in recipe.Materials:
            await cursor.execute("""
                INSERT INTO RecipeMaterials (RecipeID, MaterialID, Quantity, Measurement)
                VALUES (?, ?, ?, ?)
            """, recipe_id, mat.MaterialID, mat.Quantity, mat.Measurement)

    return {"message": "Recipe updated successfully"}

# delete recipes
@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM RecipeIngredients WHERE RecipeID = ?", (recipe_id,))
        await cursor.execute("DELETE FROM RecipeMaterials WHERE RecipeID = ?", (recipe_id,))
        await cursor.execute("DELETE FROM Recipes WHERE RecipeID = ?", (recipe_id,))
    return {"message": "Recipe deleted successfully"}
