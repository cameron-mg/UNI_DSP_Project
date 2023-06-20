# GENERAL
import datetime
import time
# DATA
import pickle
import requests
import json
import numpy as np
# ML
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

def dumpResults(properties):
    pickle.dump(properties, open("dumps/data/lastsearch.sav", "wb"))

def loadResults():
    properties = pickle.load(open("dumps/data/lastsearch.sav", "rb"))
    return properties

# Temporary property class
class PropertyPred:
    def __init__(self, property, predictiondata, modelType):
        self.property = property
        self.predictiondata = predictiondata
        self.modelType = modelType
        self.predictions = []
        self.riskfactor = 0
        self.rankingweight = 0


# Property search function (API CALL)
def propSearch(postcode):
    # Get API Search Data
    SPdata = []

    apikey = "NDRVZXZGGR"
    SPdata.append(str(apikey))

    pList = "high-rental-demand"
    SPdata.append(str(pList))

    SPdata.append(str(postcode))

    radius = 25
    SPdata.append(str(radius))

    max_age = 14
    SPdata.append(str(max_age))

    results = 10
    SPdata.append(str(results))

    # Create API call
    call = "https://api.propertydata.co.uk/sourced-properties?"+\
            "key="      +SPdata[0]+\
            "&list="    +SPdata[1]+\
            "&postcode="+SPdata[2]+\
            "&radius="  +SPdata[3]+\
            "&max_age=" +SPdata[4]+\
            "&results=" +SPdata[5]

    # Create response var from call and change to json
    response = requests.get(call)
    return_data = response.json()
    return return_data


# Property data cleaning function
def cleanProperties(properties):
    print(len(properties["properties"]))
    # Pre-Loop Declarations
    propClass = []
    today = datetime.date.today()
    pTypes = {"DETACHED" : "D", 
                 "SEMI-DETACHED": "S",
                 "TERRACED": "T",
                 "FLAT": "F",
                 "MAISONETTE": "F",
                 "OTHER": "O"}
    
    # Loading encoders
    try:
        prim_enc = pickle.load(open("dumps/enc/oac_encoder.sav", "rb"))
        aux_enc = pickle.load(open("dumps/enc/oc_encoder.sav", "rb"))
        type_enc = pickle.load(open("dumps/enc/type_encoder.sav", "rb"))
    except Exception as e:
        print(e)

    # Main cleaning loop
    for property in properties["properties"]:
        predictiondata = []
        modeltype = 0

        # Handling date data and time constraint
        year = today.year
        month = today.month
        day = today.day
        time_const = int(year*365+month*30+day-728175)
        predictiondata.append(time_const)
        predictiondata.append(year)

        # Handling property type
        check = property["type"].split(" ")[0].upper()
        if check in pTypes.keys():
            property_type = pTypes[check]
        else:
            property_type = pTypes["OTHER"]

        # Encoding and Appending
        try:
            property_type = type_enc.transform([property_type])
            predictiondata.append(property_type[0])
        except:
            break

        # Handling outcode
        try:
            outcode = property["postcode"].split(" ")[0]
            outcode = prim_enc.transform([outcode])
            predictiondata.append(outcode[0])
            modeltype = 1
        except:
            try:
                outcode = ""
                for i in property["postcode"]:
                    if i.isnumeric():
                        break
                    else:
                        outcode = outcode + i

                outcode = aux_enc.transform([outcode])
                predictiondata.append(outcode[0])
                modeltype = 2
            except:
                modeltype = 0

        # If prediciton cannot be made skip
        if modeltype == 0:
            continue
        else:
            if modeltype == 1:
                # Loading growth value
                growth_dct = pickle.load(open("dumps/dct/oac_growth_dct.sav", "rb"))
                avg_growth = growth_dct[predictiondata[3], predictiondata[2]]

                # Loading last known monthly average
                avg_dct = pickle.load(open("dumps/dct/oac_lastavg_dct.sav", "rb"))
                lastavg = avg_dct[predictiondata[3], predictiondata[2]]
                # calculate predicted current avg
                avg = lastavg + avg_growth*12*6

                # appending values
                predictiondata.append(avg)
                predictiondata.append(avg_growth)

            elif modeltype == 2:
                # Loading growth value
                growth_dct = pickle.load(open("dumps/dct/oc_growth_dct.sav", "rb"))
                avg_growth = growth_dct[predictiondata[3], predictiondata[2]]

                # Loading last known monthly average
                avg_dct = pickle.load(open("dumps/dct/oac_lastavg_dct.sav", "rb"))
                lastavg = avg_dct[predictiondata[3], predictiondata[2]]
                # calculate predicted current avg
                avg = lastavg + avg_growth*60

                # appending values
                predictiondata.append(avg)
                predictiondata.append(avg_growth)

            # Reshaping prediction data to 2d numpy
            predictiondata = np.array([predictiondata])

            # Append data to property class
            propClass.append(PropertyPred(property, predictiondata, modeltype))

    return propClass


# Function to load models and make predictions
def makePredictions(propClass):

        # Loading models
        prim_model = pickle.load(open("dumps/model/oac_test.sav", "rb"))
        aux_model = pickle.load(open("dumps/model/oc_test.sav", "rb"))

        # Making predictions
        for i in propClass:
            pred = ""
            if i.modelType == 1:
                print("\nUsing Primary Model")
                print(i.property["postcode"])
                for j in range(6):
                    print(i.predictiondata[0])
                    pred = prim_model.predict(i.predictiondata)
                    i.predictiondata[0][0] += 365
                    i.predictiondata[0][1] += 1
                    i.predictiondata[0][4] += i.predictiondata[0][5]*24
                    i.predictions.append(pred[0])
                print(i.predictions)

            elif i.modelType == 2:
                print("\nUsing Auxilliary Model")
                print(i.property["postcode"])
                for j in range(6):
                    print(i.predictiondata[0])
                    pred = aux_model.predict(i.predictiondata)
                    i.predictiondata[0][0] += 365
                    i.predictiondata[0][1] += 1
                    i.predictiondata[0][4] += i.predictiondata[0][5]*24
                    i.predictions.append(pred[0])
                print(i.predictions)

            else:
                print("Prediction Error")

        return propClass


# Function to calculate riskfactors and ranking weights
def calculateRankingWeights(propClass):
        for item in propClass:
            crimedata = requests.get("https://api.propertydata.co.uk/crime?key=NDRVZXZGGR&postcode="+item.property["postcode"]).json()
            print(crimedata)
            time.sleep(3)
            flooddata = requests.get("https://api.propertydata.co.uk/flood-risk?key=NDRVZXZGGR&postcode="+item.property["postcode"]).json()
            print(flooddata)
            time.sleep(3)       
            try:
                cpt = crimedata["crimes_per_thousand"]
                fr = flooddata["flood_risk"]    
                if fr == "None":
                    fr = 1
                elif fr == "Low":
                    fr = 2
                elif fr == "Very Low":
                    fr = 3
                elif fr == "Low":
                    fr = 4
                elif fr == "Medium":
                    fr = 5
                elif fr == "High":
                    fr = 6      
                risk = (cpt/10)*(fr**2) 
                item.riskfactor += risk 
                item.rankingweight += item.predictiondata[0][5]/item.riskfactor 
            except:
                continue
        return propClass


# Function to sort properties
def getSortedProperties(properties):
    sorted_properties = []
    if len(properties) == 1:
        return properties
    else:
        # Sorts through all properties
        while len(properties) != 0:
            index = 0
            for item in properties:
                if index == 0: # If first then set highest weight
                    highest_weight = item.rankingweight
                    index += 1
                elif item.rankingweight > highest_weight:
                    highest_weight = item.rankingweight

            # Check properties append highest
            for item in properties:
                if item.rankingweight == highest_weight:
                    sorted_properties.append(item)
                    properties.remove(item)

        return sorted_properties # return sorted properties in new list