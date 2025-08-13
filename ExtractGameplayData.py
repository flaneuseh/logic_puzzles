import pymongo 
import Database
import json 
import csv

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["gameplayDatabase"]

userDB = mydb["users"]

surveyDB = mydb["surveys"]

gameplayDB = mydb["gamePlay"]



def list_to_csv(surveys, filename):
    if len(surveys) == 0:
        print("no data")
        return 
    #keys = surveys[0].keys()
    
    columns = set()

    for survey in surveys:
        columns.update(survey.keys())


    with open(filename, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, columns)
        dict_writer.writeheader()
        dict_writer.writerows(surveys)

def clicks_to_string(clicks):
    s_clicks = sorted(clicks, key=lambda click: click["time"]) 
    names = [clicks["name"] for clicks in s_clicks]
    return names

def get_survey_for_game(gameData):
    survey = surveyDB.find_one({"pid": gameData["pid"], "userId": gameData["userId"]})

    if survey is None:
        return {} 
    else: 
        del survey["_id"]
        return survey


def get_all_data(folder):
    numHub = 0 
    all_users = userDB.find({})
    all_user_data = []  
    gameplay_data = []
    game_actions = {} 
    game_reflections = {}
    for user in list(all_users):
        user_data = dict(user)
        if not "tutorialTime" in user_data:
            user_data["tutorialTime"] = -1 
            user_data["tutorialSlide"] = -1 
        user_data["_id"] = str(user_data["_id"])
        total_time = 0 
        
        games = gameplayDB.find({"userId": user_data["_id"]}) 
        games = list(games)
        total_games = len(games)
        for game in games:
            game_data = dict(game)
            game_data["_id"] = str(game_data["_id"])
            game_data["levelMode"] = user["levelMode"]
            game_data["promptMode"] = user["promptMode"]
            game_data["logicExp"] = user["logicPuzzleExp"]
            game_data["gridExp"] = user["gridPuzzleExp"]
            if "hub" in game_data["pid"]:
                numHub += 1 

            if not "isSolved" in game_data: 
                game_data["isSolved"] = False 


            game_data.update(get_survey_for_game(game_data))
            if "actions" in game_data:
                game_actions[game_data["_id"]] = game_data["actions"]
                del game_data["actions"]
            if "reflections" in game_data:
                game_reflections[game_data["_id"]] = game_data["reflections"] 
                del game_data["reflections"]
            
            total_time += game_data["totalTime"]
            gameplay_data.append(game_data)
        
        user_data["timeSpent"] = total_time
        user_data["totalGames"] = total_games 
        all_user_data.append(user_data)
        print("Number of hub plays:", numHub)

    #print(all_user_data)
    list_to_csv(all_user_data, folder + "/user_data.csv")
    list_to_csv(gameplay_data, folder + "/gameplay_data.csv")
    
    reflection_json = json.dumps(game_reflections)
    reflect_file = open(folder + "/reflection_data.json", "w")
    reflect_file.write(reflection_json)
    reflect_file.close()

    action_json = json.dumps(game_actions)
    action_file = open(folder + "/action_data.json", "w")
    action_file.write(action_json)
    action_file.close()

if __name__ == "__main__":
    get_all_data("EscapeUserData")