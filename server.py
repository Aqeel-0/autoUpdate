from pymongo import MongoClient
from flask import Flask, request, jsonify
MONGO_URI = "mongodb+srv://skoolai:Nikunj123@cluster0.ruworvb.mongodb.net/?retryWrites=true&w=majority"

# Initialize the Flask application
app = Flask(__name__)

def connect_to_mongodb():
    global client
    print('connect funtion go callled')
    try:
        client = MongoClient(MONGO_URI)
        print("Connected to MongoDB")
        print(client)
        
    except Exception as e:
        print("Error connecting to MongoDB:", e)
connect_to_mongodb()

def get_collection():
    print(client, 'in get collection')
    db = client.get_database("test")  # Replace 'your_database_name' with your actual database name
    print(db.list_collection_names())

@app.route('/')
def flask_mongodb_atlas():
    get_collection()
    return 'job done', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
