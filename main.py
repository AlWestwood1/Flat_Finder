import requests
import json
import pickle
import os
import sys
import configparser
from urllib.parse import urlencode
from dotenv import load_dotenv
from discord import SyncWebhook, HTTPException

RESULTS_PER_PAGE = 24


class SearchRequest:
    """
    This class contains all the information required to make a search request to the rightmove API
    """

    def __init__(self, user_params: dict) -> None:
        self.location: str = user_params['location']
        self.radius: float = user_params['radius']
        self.min_price: int = user_params['min_price']
        self.max_price: int = user_params['max_price']
        self.min_room: int = user_params['min_room']
        self.max_room: int = user_params['max_room']
        self.buy_rent: str = user_params['buy_rent']

    def get_location_id(self) -> str:
        """
        Calls Rightmove API to find the best location ID match based on a given location.
        The location must be first split into tokens of 2 characters followed by a / (e.g. Camden -> CA/MD/EN)

        :return: Location ID based on the input location (str)
        """
        #Tokenise location into groups of 2 followed by a /
        tokenise_loc = "".join(char + ('/' if i % 2 == 1 else '') for i, char in enumerate(self.location.upper()))

        #Call API to return a list of location IDs. Return index 0 of this list (strongest prediction)
        try:
            url = f"https://www.rightmove.co.uk/typeAhead/uknostreet/{tokenise_loc.strip('/')}/"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            response_data = json.loads(response.text)

            return response_data["typeAheadLocations"][0]["locationIdentifier"]

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)

        except requests.exceptions.ConnectionError as e:
            print(f"Connection error occurred: {e}")
            sys.exit(1)

        except requests.exceptions.Timeout as e:
            print(f"Timeout error occurred: {e}")
            sys.exit(1)

        except requests.exceptions.RequestException as e:
            print(f"An unknown error occurred: {e}")
            sys.exit(1)


    def get_url_params(self, offset: int) -> str:
        """
        Gets the URL encoded parameters for the search request
        :param offset: Rightmove API parameter - shifts the returned results by x amount (int)
        :return: Parameters for the search request encoded in a URL format (str)
        """
        params = {
            "areaSizeUnit": "sqft",
            "channel": self.buy_rent,  # BUY or RENT
            "currencyCode": "GBP",
            "includeSSTC": "false",
            "index": offset,  # page offset
            "isFetching": "false",
            "locationIdentifier": self.get_location_id(),  # e.g.: "REGION^61294"
            "minPrice": self.min_price,
            "maxPrice": self.max_price,
            "minBedrooms": self.min_room,
            "maxBedrooms": self.max_room,
            "numberOfPropertiesPerPage": RESULTS_PER_PAGE,
            "radius": self.radius,
            "sortType": "6",
            "viewType": "LIST",
        }

        return urlencode(params)


def build_url(search_request: SearchRequest, offset: int) -> str:
    """
    Creates the Rightmove API search request URL based on the given SearchRequest object and offset
    :param search_request: SearchRequest object containing the user params
    :param offset: Rightmove API parameter - shifts the returned results by x amount (int)
    :return: URL for the Rightmove search request (str)
    """
    url = "https://www.rightmove.co.uk/api/_search?"
    params_url = search_request.get_url_params(offset)
    url += params_url
    return url

def get_properties(user_params) -> set:
    """
    Gets all properties given the user params in the config.ini file
    :param user_params: User params from the config.ini file (dict)
    :return: Set of property IDs from Rightmove for the given params (set)
    """
    #Create SearchRequest object from the user params
    sr = SearchRequest(user_params)

    try:
        #Get just the first page of results from rightmove so that the total_results can be found
        first_page = requests.get(build_url(sr, 0))
        first_page_data = json.loads(first_page.text)
        total_results = int(first_page_data["resultCount"].replace(',', ''))
        results = [p["id"] for p in first_page_data["properties"]]

        #Find the properties for all other pages (up to 1000 properties, which is the API call limit)
        max_api_result = 1000
        for offset in range(RESULTS_PER_PAGE, total_results, RESULTS_PER_PAGE):
            if offset < max_api_result:
                page_response = requests.get(build_url(sr, offset))
                page_data = json.loads(page_response.text)
                results.extend([p["id"] for p in page_data["properties"]])

        return set(results)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        sys.exit(1)

    except requests.exceptions.ConnectionError as e:
        print(f"Connection error occurred: {e}")
        sys.exit(1)

    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}")
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"An unknown error occurred: {e}")
        sys.exit(1)


def check_for_new_properties(latest_ppt_data: set) -> set:
    """
    Compares the latest set of properties against the last saved set of properties in the pickle file. Any differences will be the new properties
    :param latest_ppt_data: set of properties from the latest Rightmove API call (set)
    :return: Set of new properties (set)
    """
    #If the pickle file doesn't exist, then return an empty set (nothing to compare against)
    if not os.path.exists("property_data.pkl"):
        return set()

    #Open pickle file
    with open("property_data.pkl", "rb") as f:
        old_ppt_data = pickle.load(f)

    #Return difference between the data in the pickle file and the latest data
    return latest_ppt_data.difference(old_ppt_data)

def create_property_urls(properties: set, max_amount: int) -> list:
    """
    Creates a list of Rightmove URLs based on the given set of property IDs
    :param properties: Set of property IDs to create URLs for
    :param max_amount: Max number of URLs to create
    :return: List of Rightmove URLs for the given property IDs (List[str])
    """
    url_list = []
    for p in list(properties)[:max_amount]:
        url_list.append(f"https://www.rightmove.co.uk/properties/{p}#/")

    return url_list

def discord_post(url_list):
    """
    Posts new properties to Discord given a Discord Webhook URL in the .env file
    :param url_list: List of URLs to post to Discord
    :return: Null
    """
    #Load .env file
    try:
        load_dotenv()
    except FileNotFoundError:
        print("No .env file found. Please create a .env file with your Discord Webhook URL (named DISCORD_WEBHOOK_URL)")
        sys.exit(1)
    #Get webhook from the .env file
    try:
        webhook = SyncWebhook.from_url(os.getenv('DISCORD_WEBHOOK_URL'))
        if webhook is None:
            raise KeyError

    except KeyError:
        print("DISCORD_WEBHOOK_URL environment variable is not set")
        sys.exit(1)

    #Send a discord post for each URL in the list
    try:
        for url in url_list:
            webhook.send("A new flat has been found!\n\n"+ url + "\n")
            print("Posted to discord\n")

    except HTTPException as e:
        print(f"HTTP error occurred when connecting to Discord: {e}")
        sys.exit(1)

def get_config(filename: str) -> dict:
    config = configparser.ConfigParser()
    try:
        config.read(filename)
    except FileNotFoundError as e:
        print(f"Config file {filename} not found: {e}")
        sys.exit(1)

    required_params = ['location', 'radius', 'min_price', 'max_price', 'min_room', 'max_room', 'buy_rent']
    try:
        if "user_params" not in config:
            raise KeyError("'user_params' section not found in config file.")

        for param in required_params:
            if param not in config["user_params"] or config["user_params"][param].strip() == "":
                raise KeyError(f"Required parameter '{param}' not found in config file.")

        user_params = {
            "location": config["user_params"]["location"],
            "radius": config["user_params"].getfloat("radius"),
            "min_price": config["user_params"].getint("min_price"),
            "max_price": config["user_params"].getint("max_price"),
            "min_room": config["user_params"].getint("min_room"),
            "max_room": config["user_params"].getint("max_room"),
            "buy_rent": config["user_params"]["buy_rent"],
        }

        return user_params

    except KeyError as e:
        print(f"Key Error for config file {filename}: {e}")
        sys.exit(1)

    except TypeError as e:
        print(f"Type Error for config file {filename}: {e}")
        sys.exit(1)





def main():
    #Get params from config.ini file
    user_params = get_config("config.ini")

    #Find all properties listed on Rightmove that fill user requirements
    properties = get_properties(user_params)

    #Compare to results of last API call to find new properties
    new_properties = check_for_new_properties(properties)

    #Dump the current list of properties into a pickle file for use in the next run
    with open("property_data.pkl", "wb") as f:
        pickle.dump(properties, f)

    #Create list of URLs to send to the user on discord
    urls = create_property_urls(new_properties, 5)

    #Send user the URLs via Discord
    discord_post(urls)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An unknown error occurred: {e}")
        sys.exit(1)