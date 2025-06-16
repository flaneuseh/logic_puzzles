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

samples = list(sampleDatabase.find({}, {})) 



grammar = samples[0]["grammar"] 
brainstorm = samples[0]["brainstorms"] if "brainstorm" in samples[0] else []
categories = samples[0]["categories"]
scenarios = list(scenarioDatabase.find({}, {})) 

data = {"grammar": grammar, "brainstorms": brainstorm, "categories":categories, "scenarios": scenarios}

database = open("database.json", "w")

json.dump(data,database)

#userDB.insert_one({ "privateKey": "******", "publicKey": "Admin 2", "nextPuzzleIdx":0, "likedPuzzles":[], "grammar": {}, "evolveSessions": {"nextIdx": 0}, "categories":[]})
#userDB.insert_one({ "privateKey": "password", "publicKey": "user", "nextPuzzleIdx":0, "likedPuzzles":[], "grammar": {}, "evolveSessions": {"nextIdx": 0}, "categories":[]})


"""sampleDatabase = mydb["samples"]

#sampleDatabase.delete_many({})

with open("database.json", 'r') as file:
    database = json.load(file)
database["grammar"] = database["grammar_dict"]
del database["grammar_dict"]
i = sampleDatabase.insert_one(database)

d = sampleDatabase.find_one({})

print(d)""" 





#user = userDB.find_one_and_update({"privateKey": "password"}, {"$set": {"brainstorm.suspect.suspect.hour.before": {}}})"""



"""user = userDB.find_one({"privateKey": "password"})

result = userDB.find_one_and_update({"privateKey": "password"}, 
           {"$set": {"evolveSessions": {"nextIdx": 0}}})

print(user["likedPuzzles"])""" 


