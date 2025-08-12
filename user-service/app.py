import os
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List

app = FastAPI()

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client.user_database
user_collection = db.users

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

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# API Endpoints
@app.post("/users/", response_model=User)
def create_user(user: UserCreate):
    user_dict = user.dict()
    inserted_id = user_collection.insert_one(user_dict).inserted_id
    created_user = user_collection.find_one({"_id": inserted_id})
    return created_user

@app.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 10):
    users = list(user_collection.find().skip(skip).limit(limit))
    return users

@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, user: UserCreate):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    user_dict = user.dict()
    result = user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": user_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = user_collection.find_one({"_id": ObjectId(user_id)})
    return updated_user

@app.delete("/users/{user_id}", response_model=dict)
def delete_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    result = user_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@app.get("/")
def read_root():
    return {"message": "User service is running"}