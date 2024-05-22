from flask import Flask, request, jsonify
import numpy as np
import os
from flask_cors import CORS
from pymongo import MongoClient
import joblib

# Define MongoDB connection URI
MONGO_URI = "mongodb+srv://skoolai:Nikunj123@cluster0.ruworvb.mongodb.net/?retryWrites=true&w=majority"

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# Global variables for the model and MongoDB client
model = None
client = None

# Function to load the machine learning model
def load_model():
    global model
    try:
        model = joblib.load('pipeline')
        print("Model loaded successfully.")
    except FileNotFoundError:
        print("Error: The file 'pipeline' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred while loading the model: {e}")

# Function to connect to MongoDB
def connect_to_mongodb():
    global client
    try:
        client = MongoClient(MONGO_URI)
        print("Connected to MongoDB")
        print(client)
    except Exception as e:
        print("Error connecting to MongoDB:", e)

# Retrieve data from MongoDB
def retrieve_data():
    if client:
        try:
            # Access the database
            db = client.get_database("test")  # Replace 'your_database_name' with your actual database name

            # Access the collection
            collection = db.get_collection("mlstudents")

            # Find all documents in the collection
            data = list(collection.find({}))
            print(data)
            return data
        except Exception as e:
            print("Error retrieving data:", e)
    else:
        print("MongoDB client is not available")
    return []

def processing(data):
    for obj in data:
        attendance_array = obj['attendance']
        accumulated_status = 0
        if len(attendance_array) == 0:
            return
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

        obj['currMonthAttendance'] = current_month_attendance * 100

    return data

def prediction(data):
    output = []
    for x in data:
        del x['_id']
        del x['attendance']
        del x['presentTommorrow']
        del x['phoneNumber']
        del x['class']
        del x['__v']
        del x['name']
        if x['flag']:
            del x['flag']
            rearranged_values = [[x['rollNumber'], x['currWeekAttendance'], x['currMonthAttendance'], x['residence'],
                                  x['distance'], x['transport'], x['income'], x['participation']]]
            try:
                prediction = model.predict(rearranged_values)
                probabilities = model.predict_proba(rearranged_values)
                positive_probabilities = probabilities[:, 1]
                x['presentTommorrow'] = int(prediction[0])
                x['probability'] = float(positive_probabilities[0] * 100)
                output.append(x)
            except Exception as e:
                print(f"Error making prediction: {e}")

    return output

def update_to_db(data):
    if client:
        try:
            db = client.get_database("test")  # Replace 'your_database_name' with your actual database name
            collection = db.get_collection("mlstudents")
            for obj in data:
                id = int(obj['rollNumber'])
                new_values = {key: obj[key] for key in obj if key != "rollNumber"}
                result = collection.update_many({"rollNumber": id}, {"$set": new_values})
                print(f"{result.modified_count} documents updated.")
        except Exception as e:
            print(f"Error updating data: {e}")

@app.route('/', methods=['GET'])
def predict():
    try:
        data = retrieve_data()
        print(data)
        data = processing(data)
        new_data = prediction(data)
        update_to_db(new_data)
        return 'job done', 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    connect_to_mongodb()  # Connect to MongoDB once at the start
    load_model()  # Load the model once at the start
    app.run(host='0.0.0.0')
