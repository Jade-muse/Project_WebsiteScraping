The files contained in this repository represent the process of obtaining data from https://pokeapi.co/, a RESTful open source Pokemon API.

api_access.py constitutes the python syntax created to request JSON files from the API, extracting and storing relevant and meaningful data 
into a nested dictionary. When all requests and cleaning were completed, the dictionary was transformed into a pandas dataframe and saved as a csv file.
Care was taken to respect the pagination terms and other requirements set forth by PokeAPI.

pokemon_dex_data.csv constitutes the data obtained from the API and organized into a cohesive structure for analysis in the Data Aquisition Blog
assignment.
