# Import lines
import re
import time

import pandas as pd
import requests


# function to clean text
def flavor_cleanser(t):
    # lower all words if not lowered already
    t = t.lower()

    # Clean incorrect unicode special characters
    t = t.replace('\n\f', '\f') \
        .replace('\f',       '\n') \
        .replace('\u00ad\n', '') \
        .replace('\u00ad',   '') \
        .replace(' -\n',     ' - ') \
        .replace('-\n',      '-') \
        .replace('\n',       ' ') \
        .replace('',       ' ')

    # Collapse adjacent spaces and strip trailing whitespace.
    t = ' '.join(t.split())

    return t
    




# API all pokemon names and bst, load into an empty dataset

# Get all pokemon in single request
try:
    response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0", timeout=30)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    raise RuntimeError(
        "Problem requesting pokemon list"
    ) from e

pokemon_list = response.json()["results"]
raw = {}
species_urls = set()


for entry in pokemon_list:
    name = entry["name"]
    url = entry["url"]

    try:
        detail_res = requests.get(url, timeout=30)  # added timeout to recognize long delays
        detail_res.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Problem requesting pokemon page for {url}"
        ) from e


    data = detail_res.json()
    # Check that data is standard form, otherwise don't record
    if not data["is_default"]:
        continue
    # Double check, in case previous check misses anything
    species = data["species"]["url"]
    if species in species_urls:
        continue

    num = data["id"]

    # Map individual stats to a flat dictionary structure
    stats_dict = {
        stat_item["stat"]["name"]: stat_item["base_stat"]
        for stat_item in data["stats"]
    }

    # Calculate the Base Stat Total (BST)
    bst = sum(stats_dict.values())

    # Append to species url set for flavor text loop
    species_urls.add(species)

    # Create a complete row with name, bst, and empty vars
    raw[num] = {
        "Name": name,
        "BST": bst,
        "Truck_Mention": 0,
        "Dex_Mention": 0,
        "Food_Mention": 0,
        "Dex_Entries": []
    }
    # Rate limiter (0.1 seconds = 10 requests per second max)
    time.sleep(0.1)



# Get the Flavor text
# patterns to be used if pokedex entry is found
pattern_truck = r"\btruck\w*\b"
pattern_eat = (
    r"\b(?:"
    r"deli(?:cacy|cious)|"
    r"dish|"
    r"tast\w*|"
    r"flavor\w*|"
    r"table|"
    r"cuisine|"
    r"edible|"
    r"snack|"
    r"food|"
    r"recipe|"
    r"eat(s)?|"
    r"hunt|"
    r"prey|"
    r"preda\w*|"
    r"swallow|"
    r"food\s+source|"
    r"natural\s+enemy"
    r")\b"
)

# Using pokemon-species urls, get data
for pkm in species_urls:
    try:
        text_res = requests.get(pkm, timeout=30)
        text_res.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Problem requesting species page for {pkm}"
        ) from e
    

    species_text = text_res.json()
    num = species_text["id"]

    # Safety check in case a species page not in dataset (shouldn't happen)
    if num not in raw:
        continue

    # Extract the flavor_text for all English pokedex entries
    for entry in species_text["flavor_text_entries"]:
        if entry["language"]["name"] == "en":
            text_raw = entry["flavor_text"]

            # clean the text to remove any issues, then save to dex entries
            text_clean = flavor_cleanser(text_raw)
            raw[num]["Dex_Entries"].append(text_clean)

            # Now, a regex search of the cleaned text for other columns
            # Mentions in each dex entry are added using indicator
            indicator = int(bool(re.search(pattern_truck, text_clean)))
            raw[num]["Truck_Mention"] += indicator

            indicator = int(bool(re.search(pattern_eat, text_clean)))
            raw[num]["Food_Mention"] += indicator

    # Join list into single string, differentiating between each with \n for simpler printing
    raw[num]["Dex_Entries"] = "\n".join(raw[num]["Dex_Entries"])

    # Limit on requests (10 per second)
    time.sleep(0.1)

# Nested dictionary should now contain all pokemon, their bst, dex entries, and 2 indicator columns
# Transform into pandas dataframe
dataset = pd.DataFrame.from_dict(raw, orient="index")
dataset.reset_index(names="NationalDex_ID", inplace=True) # orients index correctly

# Now for Dex_Mention, we need to count how many times the pokemon's name value appears
# in any dex entry other than its own. 

for i in range(len(dataset)):
    name = dataset.loc[i, "Name"].lower()
    pattern = rf"\b{re.escape(name)}\b"

    count = (dataset.loc[dataset.index != i, "Dex_Entries"]
        .str.count(pattern)
        .sum()
    )
    dataset.loc[i, "Dex_Mention"] += count


# Test Run
# print(dataset.head(10))
# print(dataset.iloc[6]["Dex_Entries"])


# Store pandas dataframe using write csv
dataset.to_csv('pokemon_dex_data.csv', index=False)
