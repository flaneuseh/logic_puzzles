import pymongo

from bson.objectid import ObjectId
from copy import deepcopy

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["gameplayDatabase"]

userDB = mydb["users"]

surveyDB = mydb["surveys"]

gameplayDB = mydb["gamePlay"]


def addUser(data):
    user = userDB.insert_one(data)

    return str(user.inserted_id)

def updateUser(id, data):
    user = userDB.find_one_and_update({"_id": ObjectId(id)}, {"$set": data})
    return user is None 

def addGameplayInstance(data):
    gameplay = gameplayDB.insert_one(data)
    return str(gameplay.inserted_id)

def addGameplayAction(id, update, newAction):
    gameplay = gameplayDB.find_one_and_update({"_id": ObjectId(id)}, {"$set": update, "$push":{"actions": newAction}})
    return gameplay is None 

def addGameplayReflection(id, update, newReflection):
    gameplay = gameplayDB.find_one_and_update({"_id": ObjectId(id)}, {"$set": update, "$push":{"reflections": newReflection}})
    return gameplay is None 

def addSurvey(data):
    survey = surveyDB.insert_one(data)
    return survey is None 



