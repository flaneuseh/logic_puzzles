from pymongo import MongoClient 
import Database
import json 

  
try: 
    conn = MongoClient("mongodb://localhost:27017/") 
    print("Connected successfully!!!") 
except:   
    print("Could not connect to MongoDB") 


mydb = conn["puzzleDatabase"]

userDB = mydb["users"]

sampleDatabase = mydb["samples"]

scenarioDatabase = mydb["scenarios"]

scenarioDatabase.delete_many({}, {})
sampleDatabase.delete_many({}, {})

with open("database.json", 'r') as file:
    database = json.load(file)
samples = { "brainstorm": database["brainstorm"], "categories":database["categories"], "scenarios": database["scenarios"]}
scenarios = database["scenarios"]
i = sampleDatabase.insert_one(samples)
j = scenarioDatabase.insert_one(scenarios)

try:
    with open("data.json", 'r') as file:
        data = json.load(file)
        userDB.insert_one(data)
except:
    print("No user data found")

