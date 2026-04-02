import csv
import pymongo
import os
from dotenv import load_dotenv

load_dotenv()

client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client["inventory"]
collection = db["products"]

collection.drop()

with open("products.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        product = {
            "ProductID": int(row["ProductID"]),
            "Name": row["Name"],
            "UnitPrice": float(row["UnitPrice"]),
            "StockQuantity": int(row["StockQuantity"]),
            "Description": row["Description"]
        }
        collection.insert_one(product)

print("Done! 200 products inserted into MongoDB.")