from fastapi import APIRouter, HTTPException
from typing import List
from database import get_db_connection
from models import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

# get all products
@router.get("/", response_model=List[ProductOut])
async def get_all_products():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM Products")
        rows = await cursor.fetchall()
        return [
            {
                "ProductID": row.ProductID,
                "ProductName": row.ProductName,
                "ProductTypeID": row.ProductTypeID,
                "ProductCategory": row.ProductCategory,
                "ProductDescription": row.ProductDescription
            }
            for row in rows
        ]

# create product
@router.post("/", response_model=ProductOut)
async def add_product(product: ProductCreate):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            INSERT INTO Products (ProductName, ProductTypeID, ProductCategory, ProductDescription)
            OUTPUT INSERTED.*
            VALUES (?, ?, ?, ?)
        """, product.ProductName, product.ProductTypeID, product.ProductCategory, product.ProductDescription)
        row = await cursor.fetchone()
        return {
            "ProductID": row.ProductID,
            "ProductName": row.ProductName,
            "ProductTypeID": row.ProductTypeID,
            "ProductCategory": row.ProductCategory,
            "ProductDescription": row.ProductDescription
        }

# update product
@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, product: ProductUpdate):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            UPDATE Products
            SET ProductName = ?, ProductTypeID = ?, ProductCategory = ?, ProductDescription = ?
            WHERE ProductID = ?
        """, product.ProductName, product.ProductTypeID, product.ProductCategory, product.ProductDescription, product_id)

        await cursor.execute("SELECT * FROM Products WHERE ProductID = ?", product_id)
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        return {
            "ProductID": row.ProductID,
            "ProductName": row.ProductName,
            "ProductTypeID": row.ProductTypeID,
            "ProductCategory": row.ProductCategory,
            "ProductDescription": row.ProductDescription
        }

# delete product
@router.delete("/{product_id}")
async def delete_product(product_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM Products WHERE ProductID = ?", product_id)
    return {"message": "Product deleted successfully"}
