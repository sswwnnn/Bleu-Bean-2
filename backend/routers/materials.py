from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date
from database import get_db_connection

router = APIRouter(
    prefix="/materials",
    tags=["materials"]
)

# thresholds for stock status
material_thresholds = {
    "pcs": 10,
    "box": 2,
    "pack": 5,
    "small": 10,
    "medium": 10,
    "large": 10
}

def get_material_status(quantity: float, measurement: str):
    if quantity <= 0:
        return "Not Available"
    elif quantity <= material_thresholds.get(measurement, 1):
        return "Low on Stock"
    return "Available"

class MaterialBase(BaseModel):
    MaterialName: str
    MaterialQuantity: float
    MaterialMeasurement: str = None
    DateAdded: date  

class MaterialOut(MaterialBase):
    MaterialID: int
    Status: str

# create
@router.post("/", response_model=MaterialOut)
async def add_material(material: MaterialBase):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        status = get_material_status(material.MaterialQuantity, material.MaterialMeasurement)
        await cursor.execute("""
            INSERT INTO Materials (MaterialName, MaterialQuantity, MaterialMeasurement, DateAdded, Status)
            OUTPUT INSERTED.*
            VALUES (?, ?, ?, ?, ?)
        """, material.MaterialName, material.MaterialQuantity,
             material.MaterialMeasurement, material.DateAdded, status)
        row = await cursor.fetchone()
        return dict(zip([col[0] for col in cursor.description], row))

# get all materials
@router.get("/", response_model=List[MaterialOut])
async def get_all_materials():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Materials")
        rows = await cursor.fetchall()
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]

# update materials
@router.put("/{material_id}", response_model=MaterialOut)
async def update_material(material_id: int, material: MaterialBase):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        status = get_material_status(material.MaterialQuantity, material.MaterialMeasurement)
        await cursor.execute("""
            UPDATE Materials
            SET MaterialName = ?, MaterialQuantity = ?, MaterialMeasurement = ?, DateAdded = ?, Status = ?
            WHERE MaterialID = ?
        """, material.MaterialName, material.MaterialQuantity,
             material.MaterialMeasurement, material.DateAdded, status, material_id)
        await cursor.execute("SELECT * FROM Materials WHERE MaterialID = ?", material_id)
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Material not found")
        return dict(zip([col[0] for col in cursor.description], row))

# delete materials
@router.delete("/{material_id}")
async def delete_material(material_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM Materials WHERE MaterialID = ?", material_id)
    return {"message": "Material deleted successfully"}
