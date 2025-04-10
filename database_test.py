from pymongo import MongoClient 
import json 
  
try: 
    conn = MongoClient("mongodb://localhost:27017/") 
    print("Connected successfully!!!") 
except:   
    print("Could not connect to MongoDB") 




mydb = conn["puzzleDatabase"]

"""userDB = mydb["users"]

scenarioDatabase = mydb["community"] 

scenarioDatabase.delete_many({})

scenarios = list(scenarioDatabase.find({}, {})) 

print(scenarios)"""





#userDB.insert_one({ "privateKey": "admin", "publicKey": "Admin 1", "nextPuzzleIdx":0, "likedPuzzles":[], "grammar": {}, "evolveSessions": {"nextIdx": 0}, "categories":[]})
#userDB.insert_one({ "privateKey": "password", "publicKey": "user", "nextPuzzleIdx":0, "likedPuzzles":[], "grammar": {}, "evolveSessions": {"nextIdx": 0}, "categories":[]})


sampleDatabase = mydb["samples"]
sampleDatabase.delete_many({})

with open("database.json", 'r') as file:
    database = json.load(file)
database["grammar"] = database["grammar_dict"]
del database["grammar_dict"]
i = sampleDatabase.insert_one(database)

database = sampleDatabase.find_one({})

print(database)





#user = userDB.find_one_and_update({"privateKey": "password"}, {"$set": {"brainstorm.suspect.suspect.hour.before": {}}})"""



"""user = userDB.find_one({"privateKey": "password"})

result = userDB.find_one_and_update({"privateKey": "password"}, 
           {"$set": {"evolveSessions": {"nextIdx": 0}}})

print(user["likedPuzzles"])""" 


