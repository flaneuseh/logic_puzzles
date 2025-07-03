import pymongo

from bson.objectid import ObjectId
from copy import deepcopy

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["gameplayDatabase"]

userDB = mydb["users"]

surveyDB = mydb["surveys"]

gameplayDB = mydb["gamePlay"]


userDB.delete_many({})

surveyDB.delete_many({})
gameplayDB.delete_many({})