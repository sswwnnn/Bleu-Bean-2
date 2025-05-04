from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date
from database import get_db_connection
from models import MerchandiseCreate, MerchandiseUpdate, MerchandiseOut

router = APIRouter(
    prefix="/merchandise",
    tags=["merchandise"]
)

# status threshold 
def determine_status(quantity: int) -> str:
    if quantity == 0:
        return "Not Available"
    elif quantity < 10:
        return "Low Stock"
    else:
        return "Available"

# create merchandise
@router.post("/", response_model=MerchandiseOut)
async def create_merchandise(data: MerchandiseCreate):
    status = determine_status(data.MerchandiseQuantity)
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            INSERT INTO Merchandise (MerchandiseName, MerchandiseQuantity, MerchandiseDateAdded, Status)
            OUTPUT INSERTED.MerchandiseID, INSERTED.MerchandiseName, INSERTED.MerchandiseQuantity, 
                   INSERTED.MerchandiseDateAdded, INSERTED.Status
            VALUES (?, ?, ?, ?)
        """, data.MerchandiseName, data.MerchandiseQuantity, data.MerchandiseDateAdded, status)
        inserted = await cursor.fetchone()

    return {
        "MerchandiseID": inserted.MerchandiseID,
        "MerchandiseName": inserted.MerchandiseName,
        "MerchandiseQuantity": inserted.MerchandiseQuantity,
        "MerchandiseDateAdded": inserted.MerchandiseDateAdded,
        "Status": inserted.Status
    }

# get all merchandise
@router.get("/", response_model=List[MerchandiseOut])
async def get_all_merchandise():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Merchandise")
        items = await cursor.fetchall()

    return [
        {
            "MerchandiseID": row.MerchandiseID,
            "MerchandiseName": row.MerchandiseName,
            "MerchandiseQuantity": row.MerchandiseQuantity,
            "MerchandiseDateAdded": row.MerchandiseDateAdded,
            "Status": row.Status
        }
        for row in items
    ]

# get by ID
# @router.get("/{merchandise_id}", response_model=MerchandiseOut)
# async def get_merchandise(merchandise_id: int):
#     conn = await get_db_connection()
#     async with conn.cursor() as cursor:
#         await cursor.execute("SELECT * FROM Merchandise WHERE MerchandiseID = ?", merchandise_id)
#         row = await cursor.fetchone()

#     if not row:
#         raise HTTPException(status_code=404, detail="Merchandise not found")

#     return {
#         "MerchandiseID": row.MerchandiseID,
#         "MerchandiseName": row.MerchandiseName,
#         "MerchandiseQuantity": row.MerchandiseQuantity,
#         "MerchandiseDateAdded": row.MerchandiseDateAdded,
#         "Status": row.Status
#     }

# update merchandise
@router.put("/{merchandise_id}")
async def update_merchandise(merchandise_id: int, data: MerchandiseUpdate):
    new_status = determine_status(data.MerchandiseQuantity)
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Merchandise WHERE MerchandiseID = ?", merchandise_id)
        exists = await cursor.fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Merchandise not found")

        await cursor.execute("""
            UPDATE Merchandise
            SET MerchandiseName = ?, MerchandiseQuantity = ?, MerchandiseDateAdded = ?, Status = ?
            WHERE MerchandiseID = ?
        """, data.MerchandiseName, data.MerchandiseQuantity, data.MerchandiseDateAdded, new_status, merchandise_id)

    return {"message": "Merchandise updated successfully", "Status": new_status}

# delete merchandise
@router.delete("/{merchandise_id}")
async def delete_merchandise(merchandise_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Merchandise WHERE MerchandiseID = ?", merchandise_id)
        exists = await cursor.fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Merchandise not found")

        await cursor.execute("DELETE FROM Merchandise WHERE MerchandiseID = ?", merchandise_id)

    return {"message": "Merchandise deleted successfully"}
