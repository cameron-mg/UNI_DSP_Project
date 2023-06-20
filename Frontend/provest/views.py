# Django
from provest.models import *
from provest.forms import *
from django.shortcuts import render, redirect
from provest.integ import propSearch, cleanProperties, makePredictions, calculateRankingWeights, getSortedProperties, PropertyPred, loadResults, dumpResults
import matplotlib.pyplot as plt
import io
from django.http import HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout


# Home function
def home(request):
    return render(request, 'provest/home.html')


# Website search page
def search(request):
    form = postcodeForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():
            postcode = form.cleaned_data["postcode"]

            # Fetching Properties
            try:
                stage = "Fetching Properties..."
                # render(request, 'provest/search.html', {"stage":stage})
                noncleaned_properties = propSearch(postcode)
                print(noncleaned_properties)
            except:
                searched = False
                error = "Error: Property Fetching!"
                return render(request, 'provest/search.html', {"form":form, "searched":searched, "error":error})
            

            # Cleaning Data
            try:
                stage = "Cleaning Data..."
                # render(request, 'provest/search.html', {"stage":stage})
                cleaned_properties = cleanProperties(noncleaned_properties)
            except:
                searched = False
                error = "Error: Data Cleaning!"
                return render(request, 'provest/search.html', {"form":form, "searched":searched, "error":error})
            

            # Predicting Future Prices
            try:
                stage = "Predicting Future Prices..."
                # render(request, 'provest/search.html', {"stage":stage})
                predicted_properties = makePredictions(cleaned_properties)
            except:
                searched = False
                error = "Error: Price Prediction!"
                return render(request, 'provest/search.html', {"form":form, "searched":searched, "error":error})


            # Ranking Properties
            try:
                stage = "Ranking Properties..."
                render(request, 'provest/search.html', {"stage":stage})
                ranked_properties = calculateRankingWeights(predicted_properties)
            except:
                searched = False
                error = "Error: Property Ranking!"
                return render(request, 'provest/search.html', {"form":form, "searched":searched, "error":error})


            # Sorting Properties
            try:
                stage = "Sorting Properties..."
                render(request, 'provest/search.html', {"stage":stage})
                sorted_properties = getSortedProperties(ranked_properties)
            except:
                searched = False
                error = "Error: Sorting Properties!"
                return render(request, 'provest/search.html', {"form":form, "searched":searched, "error":error})

            # Dumping last search results
            dumpResults(sorted_properties)
            
            return redirect("searchdisplay")
                 
        else:
            searched = False
            return render(request, 'provest/search.html', {"form":form, "searched":searched})
        
    else:
        searched = False
        return render(request, 'provest/search.html', {"form":form, "searched":searched})


# Function to view searched properties
def searchdisplay(request):
    properties = loadResults()
    return render(request, 'provest/searchdisplay.html', {"properties":properties})


# Function to view property details
def propdetails(request, p_id):
    properties = loadResults()
    for prop in properties:
        if prop.property["id"] == p_id:
            passed = prop

    return render(request, 'provest/propdetails.html', {"property":passed})


# Create property graph
def prop_graph(request, p_id):
    properties = loadResults()
    for prop in properties:
        if prop.property["id"] == p_id:
            passed = prop

            # Create the graph
            fig, ax = plt.subplots()
            ax.plot(passed.predictions)

            # Save the plot to object
            byteo = io.BytesIO()
            plt.savefig(byteo, format='png')
            byteo.seek(0)

            # Return graph as response to be used as png
            response = HttpResponse(byteo.getvalue(), content_type='image/png')
            return response


# Function to view saved properties
def savedproperties(request):
    return render(request, 'provest/savedproperties.html')

# Function to allow the user to login
def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request=request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)

            if user is not None:
                login(user)
            else:
                error = "NULL USER"
                return render(request, "registration/login.html", {"form":form, "error":error})
        else:
            form = AuthenticationForm()
            error = "Invalid Form"
            return render(request, "registration/login.html", {"form":form, "error":error})
    else:
        form = AuthenticationForm()
        return render(request, "registration/login.html", {"form":form, "error":error})
    
def logout_request(request):
    logout(request)
    return redirect("home")