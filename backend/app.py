# Imports
import requests
from dotenv import load_dotenv
load_dotenv()
import os

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

    # Populate each sub array
    for movieDictionary in movieDictionaries:
        originalTitles.append(movieDictionary["original_title"])
        overviews.append(movieDictionary["overview"])
        releaseDates.append(movieDictionary["release_date"])
        voteAverages.append(movieDictionary["vote_average"])
        # TODO: Add background images for each movie

    # Add each array to the parent array
    arrays = [originalTitles, overviews, releaseDates, voteAverages]
    for array in arrays:
        movieMatrix.append(array)

    # Return the matrix to the frontend for processing
    return movieMatrix

# Testing
print(extractRequired(getMovies("", "Kevin James", "Comedy", "Netflix")))