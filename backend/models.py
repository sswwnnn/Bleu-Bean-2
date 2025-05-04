from pydantic import BaseModel
from datetime import date
from typing import Optional

class IngredientBase(BaseModel):
    IngredientName: str
    Amount: float
    Measurement: str
    BestBeforeDate: date
    ExpirationDate: date

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(IngredientBase):
    pass

class IngredientOut(IngredientBase):
    IngredientID: int
    Status: str

    class Config:
        from_attributes = True

class ProductType(BaseModel):
    ProductTypeID: int
    TypeName: str

class ProductCreate(BaseModel):
    ProductName: str
    ProductTypeID: int
    ProductCategory: str
    ProductDescription: Optional[str] = None

class ProductOut(ProductCreate):
    ProductID: int

class ProductUpdate(ProductCreate):
    pass

class MerchandiseBase(BaseModel):
    MerchandiseName: str
    MerchandiseQuantity: int
    MerchandiseDateAdded: date

class MerchandiseCreate(MerchandiseBase):
    pass

class MerchandiseUpdate(MerchandiseBase):
    pass

class MerchandiseOut(MerchandiseBase):
    MerchandiseID: int
    Status: str
