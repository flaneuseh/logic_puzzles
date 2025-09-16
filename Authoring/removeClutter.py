from pymongo import MongoClient 
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

admins_public_keys = ["Admin 1", "Admin 2"]

evolveSessions = mydb["evolveSessions"]

sessions = mydb["sessions"]

posted_puzzles_hybrid = mydb["community_hybrid"]

posted_puzzles_serious = mydb["community_serious"]

survey_db = mydb["surveys"]

def remove_user(publicKey):
    userDB.find_one_and_delete({"publicKey": publicKey})
    sessions.delete_many({"user": publicKey})
    survey_db.delete_many({"username": publicKey})
    posted_puzzles_hybrid.delete_many({"username": publicKey})

def clearEvolve():
    evolveSessions.delete_many({})

def deleteScenario(name): 
    scen = scenarioDatabase.find_one_and_delete({"name": name})

user_to_remove = ["Test user 1", "Test User 2", "Test user 3", "user", "serious", "casual", "Tutorial User", "Saffron", "Sunflower"]

removed = [remove_user(user) for user in user_to_remove]

deleteScenario("custom scenario")