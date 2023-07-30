# Imports
from flask import Flask, request, render_template, redirect, url_for
import requests
from dotenv import load_dotenv
load_dotenv()
import os
import json
import urllib

# Define Flask application
app = Flask(__name__)

# Define a place to store movie information for the frontend
movieInformation = []

# Headers 
headers = {
    "accept": "application/json",
    "Authorization": os.getenv("HEADER_AUTHORIZATION")
}

# TMDB API Key
apiKey = os.getenv('API_KEY')

# TMDB API URL
url = f'https://api.themoviedb.org/3/discover/movie'

# Get 

# Get the TMDB ID of a person
def getPersonId(name):
    # Get a response
    searchUrl = f'https://api.themoviedb.org/3/search/person'
    parameters = {
        'api_key': apiKey,
        'query': name
    }

    response = requests.get(searchUrl, params = parameters)
    data = response.json()

    # Parse the response for the id and return 
    if response.status_code == 200 and 'results' in data:
        results = data['results']
        if results:
            return results[0]['id']

    # If no id is found, return an empty string 
    return ""

# Get a list of movies based on user preferences 
def getMovies(directorName, castMemberName, genre, streamingService):
    # Start by defining the TMDB Id of each user input
    directorId = getPersonId(directorName)
    castMemberId = getPersonId(castMemberName)
    genreId = 0

    # Get the genre Id and store it in genreId
    genreUrl = "https://api.themoviedb.org/3/genre/movie/list"

    response = requests.get(genreUrl, headers=headers).json()
    for dictionary in response["genres"]:
        if genre == dictionary["name"]:
            genreId = dictionary["id"]
            break

    # With all the TMDB Id's filled in, get an initial movie list        
    if directorId is not None and castMemberId is not None:
        parameters = {
            'api_key': apiKey,
            'with_genres': genreId,
            'with_crew': directorId,
            'with_cast': castMemberId,
        }

        response = requests.get(url, params=parameters)
        data = response.json()
        initialMovieList = data['results']

        # Expand and filter down the initial movie list
        totalPages = data['total_pages']
        moviesPerPage = 20 
        moviesToFetch = min(50, totalPages * moviesPerPage)

        for page in range(2, (moviesToFetch // moviesPerPage) + 2):
            parameters['page'] = page
            response = requests.get(url, params = parameters)
            data = response.json()
            initialMovieList.extend(data['results'])

            if len(initialMovieList) >= moviesToFetch:
                break

        # If user doesn't have any streaming service preference, return the initial movie list
        if len(streamingService) == 0:
            return initialMovieList
        
        else:
            # Otherwise, filter down the list by streaming service
            moviesStreamingService = []

            for movie in initialMovieList:
                response = requests.get(f"https://api.themoviedb.org/3/movie/{movie['id']}/watch/providers", headers = headers)
                data = response.json()

                for countryCode, countryData in data["results"].items():
                    if countryCode == "US":
                        if "flatrate" in countryData:
                            for provider in countryData["flatrate"]:
                                providerName = provider["provider_name"]
                                if providerName == streamingService:
                                    moviesStreamingService.append(movie)

            # Return the list of movies
            return moviesStreamingService

# Extract needed information from getMovies()
def extractRequired(movieDictionaries):
    # Parent array for all sub arrays
    movieMatrix = []

    # Store each piece of information in a separate array
    originalTitles = []
    overviews = []
    releaseDates = []
    voteAverages = []
    posterPaths = []
    posterUrls = []

    # Populate each sub array
    for movieDictionary in movieDictionaries:
        originalTitles.append(movieDictionary["original_title"])
        overviews.append(movieDictionary["overview"])
        releaseDates.append(movieDictionary["release_date"])
        voteAverages.append(movieDictionary["vote_average"])
        posterPaths.append(movieDictionary["poster_path"])

    # Get each poster path URL, store in posterUrls
    for posterPath in posterPaths:
        posterUrls.append(f"https://image.tmdb.org/t/p/original{posterPath}")

    # Add each array to the parent array
    arrays = [originalTitles, overviews, releaseDates, voteAverages, posterUrls]
    for array in arrays:
        movieMatrix.append(array)

    # Return the matrix to the frontend for processing
    return movieMatrix

# Parent function for both subfunctions
def officialMovieInformation(streamingService, genre, director, castMember):
    return extractRequired(getMovies(director, castMember, genre, streamingService))

# Route for user input
@app.route("/form", methods = ["POST", "GET"])
def form():
    director = ""
    castMember = ""
    genre = ""
    streamingService = ""

    if request.method == "POST":
        director = str(request.form["director"])
        castMember = str(request.form["castMember"])
        genre = str(request.form["genre"])
        streamingService = str(request.form["streamingService"])
        movies = officialMovieInformation(streamingService, genre, director, castMember)
        moviesJson = json.dumps(movies)  # Convert the 2D array to a JSON string
        encodedMovies = urllib.parse.quote(moviesJson)  # Encode the JSON string for the URL
        return redirect(url_for("recommendations", movies = encodedMovies))

    genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Science Fiction", "Thriller", "TV Movie", "War", "Western"];
    return render_template("form.html", genres = genres)

# Movie recommendation route
@app.route("/recommendations")
def recommendations():
    encodedMovies = request.args.get("movies", None)
    decodedMovies = urllib.parse.unquote(encodedMovies) 
    movies = json.loads(decodedMovies)  
    return render_template("movies.html", movies = movies)