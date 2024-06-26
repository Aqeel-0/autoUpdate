from pymongo import MongoClient
from joblib import load
model = load('pipeline')
# Define MongoDB connection URI
MONGO_URI = "mongodb+srv://skoolai:Nikunj123@cluster0.ruworvb.mongodb.net/?retryWrites=true&w=majority"

# Connect to MongoDB
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
    else:
        print("MongoDB client is not available")

def processing(data):
    
    for obj in data:
        
        attendance_array = obj['attendance']
        
        accumulated_status = 0
        # Ensure there are at least 5 elements in the array before getting the last 5 elements
        if len(attendance_array) == 0:
            return  
        if len(attendance_array) >= 5:
            # Get the last 5 objects from the attendance array
            last_5_attendance = attendance_array[-5:]
            # Accumulate the values of the 'status' variable
            accumulated_status = sum(entry['status'] for entry in last_5_attendance)
            current_week_attendance = accumulated_status
            
        else:
            # Get all elements in the array and calculate their sum
            accumulated_status = sum(entry['status'] for entry in attendance_array)
            current_week_attendance = accumulated_status
            
        obj['currWeekAttendance'] = current_week_attendance
        accumulated_status = 0
        # Ensure there are at least 5 elements in the array before getting the last 5 elements

        if len(attendance_array) >= 30:
            # Get the last 5 objects from the attendance array
            last_30_attendance = attendance_array[-30:]
            # Accumulate the values of the 'status' variable
            accumulated_status = sum(entry['status'] for entry in last_30_attendance)
            current_month_attendance = (accumulated_status/30)*100
            
        else:
            # Get all elements in the array and calculate their sum
            accumulated_status = sum(entry['status'] for entry in attendance_array)
            current_month_attendance = accumulated_status/len(attendance_array)
            
        obj['currMonthAttendance'] = current_month_attendance*100
        
    
    return data


    


def prediction(data):
    output = []
    
    for x in data:
        del x['_id']
        del x['attendance']
        del x ['presentTommorrow']
        del x ['phoneNumber']
        del x['class']
        del x['__v']
        del x['name']
        if x['flag']:
            del x['flag']
            values = list(x.values())

            rearranged_values = [[x['rollNumber'], x['currWeekAttendance'], x['currMonthAttendance'], x['residence'], 
                                  x['distance'], x['transport'], x['income'], x['participation']]]
            #arr = [[7112, 2, 95, 'PG', 47, 'Car', 27, 0]]
            prediction = model.predict(rearranged_values)
            probabilities = model.predict_proba(rearranged_values)
            positive_probabilities = probabilities[:, 1]
            x['presentTommorrow'] = int(prediction[0])
            x['probability'] = float(positive_probabilities[0]*100)
            
            output.append(x)
    
    return output

        
def updateToDb(client, data):
    db = client.get_database("test")  # Replace 'your_database_name' with your actual database name

    # Access the collection
    collection = db.get_collection("mlstudents")
    for obj in data:
        id = int(obj['rollNumber'])
        new_values = {key: obj[key] for key in obj if key != "rollNumber"}
        # for x in new_values:
        #     print(type(new_values[x]))
        result = collection.update_many({"rollNumber": id}, {"$set": new_values})
        print(result.modified_count, "documents updated.")

        
    
    
    
# Main function
def main():
    # Connect to MongoDB
    client = connect_to_mongodb()

    # Retrieve data
    data = retrieve_data(client)
    
    data = processing(data)
    
    newData = prediction(data)
    updateToDb(client, newData)

# Execute main function
if __name__ == "__main__":
    main()
