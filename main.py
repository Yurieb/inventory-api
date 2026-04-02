from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Inventory Management API",
    description="API for managing product inventory",
    version="1.0.0"
)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["inventory"]
collection = db["products"]


class Product(BaseModel):
    ProductID: int = Field(..., description="Unique product ID")
    Name: str = Field(..., description="Product name")
    UnitPrice: float = Field(..., gt=0, description="Price in USD")
    StockQuantity: int = Field(..., ge=0, description="Stock quantity")
    Description: str = Field(..., description="Product description")


@app.get("/getSingleProduct")
def get_single_product(id: int):
    product = collection.find_one({"ProductID": id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/getAll")
def get_all():
    products = list(collection.find({}, {"_id": 0}))
    return products


@app.post("/addNew")
def add_new(product: Product):
    existing = collection.find_one({"ProductID": product.ProductID})
    if existing:
        raise HTTPException(status_code=400, detail="ProductID already exists")
    collection.insert_one(product.dict())
    return {"message": "Product added successfully"}


@app.delete("/deleteOne")
def delete_one(id: int):
    result = collection.delete_one({"ProductID": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": f"Product {id} deleted successfully"}


@app.get("/startsWith")
def starts_with(letter: str):
    if len(letter) != 1 or not letter.isalpha():
        raise HTTPException(status_code=400, detail="Please provide a single letter")
    products = list(collection.find(
        {"Name": {"$regex": f"^{letter}", "$options": "i"}},
        {"_id": 0}
    ))
    return products


@app.get("/paginate")
def paginate(start: int, end: int):
    if start > end:
        raise HTTPException(status_code=400, detail="Start must be less than End")
    products = list(collection.find(
        {"ProductID": {"$gte": start, "$lte": end}},
        {"_id": 0}
    ).limit(10))
    return products


@app.get("/convert")
def convert(id: int):
    product = collection.find_one({"ProductID": id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        rate = response.json()["rates"]["EUR"]
    except Exception:
        raise HTTPException(status_code=503, detail="Could not fetch exchange rate")
    euro_price = round(product["UnitPrice"] * rate, 2)
    return {
        "ProductID": id,
        "Name": product["Name"],
        "PriceUSD": product["UnitPrice"],
        "PriceEUR": euro_price,
        "ExchangeRate": rate
    }