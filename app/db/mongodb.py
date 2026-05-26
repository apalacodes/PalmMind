import motor.motor_asyncio

import os
from dotenv import load_dotenv

client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client["mydatabase"]

bookings_collection = db['bookings']
metadata_collection = db['chunks_metadata']

