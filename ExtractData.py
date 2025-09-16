import pymongo 
import Authoring.Database as Database
import json 

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["puzzleDatabase"]

userDB = mydb["users"]

sampleDatabase = mydb["samples"]

scenarioDatabase = mydb["scenarios"]

admins_public_keys = ["Admin 1", "Admin 2"]

evolveSessions = mydb["evolveSessions"]

sessions = mydb["sessions"]

posted_puzzles_hybrid = mydb["community_hybrid"]

posted_puzzles_serious = mydb["community_serious"]

survey_db = mydb["surveys"]
import csv

def list_to_csv(surveys, filename):
    if len(surveys) == 0:
        print("no data")
        return 
    keys = surveys[0].keys()

    with open(filename, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(surveys)

def clicks_to_string(clicks):
    s_clicks = sorted(clicks, key=lambda click: click["time"]) 
    names = [clicks["name"] for clicks in s_clicks]
    return names

def get_data_for_user(username):
    user = userDB.find_one({"publicKey": username})
    

    surveys = list(survey_db.find({"username": username}))
    sess= list(sessions.find({"user": username}))

    total_time = 0 
    total_cas = 0 
    total_serious = 0 
    total_nut = 0 
    total_downloads = 0 

    for s in sess:
        total_time += s["totalTime"]
        total_cas += s["totalCasual"]
        total_serious += s["totalSerious"]
        total_nut += s["totalNeutral"]

        downloads = [click for click in s["clicks"] if click["name"] == "download"]
        total_downloads += len(downloads)

    new_surveys = []
    for s in surveys:
        new_s = s["CSI"]
        new_s.update(s["openResponses"])
        new_surveys.append(new_s)

    
    userData = {"username": username, "mode": user["mode"],
                "totalTime":total_time, "totalCasual": total_cas, "totalSerious":total_serious, "totalNeutral":total_nut, 
                "numberSessions":len(sess), "numberSurveys": len(surveys), "numberLikedPuzzles": len(user["likedPuzzles"]), "downloads": total_downloads }
    
    return userData, new_surveys, sess

def save_data(passwords):
    all_data = []
    for password in passwords: 
        data, surveys, sess = get_data_for_user(password)
        all_data.append(data)

        for s in sess:
            s["clicks"] = clicks_to_string(s["clicks"])
        
        list_to_csv(surveys, "AuthoringUserData/Surveys/" + data["username"] + ".csv")
        list_to_csv(sess, "AuthoringUserData/Sessions/" + data["username"] + ".csv")
    
    list_to_csv(all_data, "AuthoringUserData/user_data.csv")




passwords = ['Admin 1', 'user', 'Serious User', 'Casual User']
save_data(passwords)