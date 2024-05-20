from flask import Flask, request, jsonify
import numpy as np
from flask_cors import CORS
from pymongo import MongoClient
from joblib import load

# Load the model once
model = load('pipeline')

# Define MongoDB connection URI
MONGO_URI = "mongodb+srv://skoolai:Nikunj123@cluster0.ruworvb.mongodb.net/?retryWrites=true&w=majority"

# Initialize Flask app
app = Flask(__name__)
CORS(app)

def connect_to_mongodb():
    try:
        client = MongoClient(MONGO_URI)
        print("Connected to MongoDB")
        return client
    except Exception as e:
        print("Error connecting to MongoDB:", e)
        return None

# Retrieve data from MongoDB
def retrieve_data(client):
    if client:
        try:
            # Access the database
            db = client.get_database("test")  # Replace 'your_database_name' with your actual database name

            # Access the collection
            collection = db.get_collection("mlstudents")

            # Find all documents in the collection
            data = list(collection.find({}))
            
            return data
        except Exception as e:
            print("Error retrieving data:", e)
            return []
    else:
        print("MongoDB client is not available")
        return []

def processing(data):
    for obj in data:
        attendance_array = obj['attendance']
        accumulated_status = 0

        # Ensure there are at least 5 elements in the array before getting the last 5 elements
        if len(attendance_array) == 0:
            continue
        if len(attendance_array) >= 5:
            last_5_attendance = attendance_array[-5:]
            accumulated_status = sum(entry['status'] for entry in last_5_attendance)
            current_week_attendance = accumulated_status
        else:
            accumulated_status = sum(entry['status'] for entry in attendance_array)
            current_week_attendance = accumulated_status
            
        obj['currWeekAttendance'] = current_week_attendance
        accumulated_status = 0

        if len(attendance_array) >= 30:
            last_30_attendance = attendance_array[-30:]
            accumulated_status = sum(entry['status'] for entry in last_30_attendance)
            current_month_attendance = (accumulated_status / 30) * 100
        else:
            accumulated_status = sum(entry['status'] for entry in attendance_array)
            current_month_attendance = (accumulated_status / len(attendance_array)) * 100
            
        obj['currMonthAttendance'] = current_month_attendance
    
    return data

def prediction(data):
    output = []
    for x in data:
        x_copy = x.copy()  # Work on a copy to avoid modifying the original data
        x_copy.pop('_id', None)
        x_copy.pop('attendance', None)
        x_copy.pop('presentTommorrow', None)
        x_copy.pop('phoneNumber', None)
        x_copy.pop('class', None)
        x_copy.pop('__v', None)
        x_copy.pop('name', None)

        if x_copy.get('flag'):
            x_copy.pop('flag', None)
            rearranged_values = [[
                x_copy['rollNumber'], x_copy['currWeekAttendance'], x_copy['currMonthAttendance'],
                x_copy['residence'], x_copy['distance'], x_copy['transport'],
                x_copy['income'], x_copy['participation']
            ]]

            prediction = model.predict(rearranged_values)
            probabilities = model.predict_proba(rearranged_values)
            positive_probabilities = probabilities[:, 1]

            x['presentTommorrow'] = int(prediction[0])
            x['probability'] = float(positive_probabilities[0] * 100)

            output.append(x)
    
    return output

def updateToDb(client, data):
    db = client.get_database("test")  # Replace 'your_database_name' with your actual database name
    collection = db.get_collection("mlstudents")
    for obj in data:
        roll_number = int(obj['rollNumber'])
        new_values = {key: obj[key] for key in obj if key != "rollNumber"}
        result = collection.update_many({"rollNumber": roll_number}, {"$set": new_values})
        print(result.modified_count, "documents updated.")

@app.route('/', methods=['GET'])
def predict():
    try:
        client = connect_to_mongodb()
        data = retrieve_data(client)
        data = processing(data)
        newData = prediction(data)
        updateToDb(client, newData)
        return 'Job done', 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000)
