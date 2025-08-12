import os
import time
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List

app = FastAPI()

# MongoDB connection with retry logic
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = None
for i in range(10):
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info() # force connection on a request
        print("Connected to MongoDB!")
        break
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}, retrying...")
        time.sleep(5)

if client is None:
    raise Exception("Could not connect to MongoDB")

db = client.product_database
product_collection = db.products

# Pydantic models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class ProductBase(BaseModel):
    name: str
    price: float

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# API Endpoints
@app.post("/products/", response_model=Product)
def create_product(product: ProductCreate):
    product_dict = product.dict()
    inserted_id = product_collection.insert_one(product_dict).inserted_id
    created_product = product_collection.find_one({"_id": inserted_id})
    return created_product

@app.get("/products/", response_model=List[Product])
def read_products(skip: int = 0, limit: int = 10):
    products = list(product_collection.find().skip(skip).limit(limit))
    return products

@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    product = product_collection.find_one({"_id": ObjectId(product_id)})
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: str, product: ProductCreate):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    product_dict = product.dict()
    result = product_collection.update_one({"_id": ObjectId(product_id)}, {"$set": product_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    updated_product = product_collection.find_one({"_id": ObjectId(product_id)})
    return updated_product

@app.delete("/products/{product_id}", response_model=dict)
def delete_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    result = product_collection.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@app.get("/")
def read_root():
    return {"message": "Product service is running"}