import requests
import json
import pickle
import os
from urllib.parse import urlencode
from dotenv import load_dotenv
from discord import SyncWebhook

RESULTS_PER_PAGE = 24
load_dotenv()

class SearchRequest:
    def __init__(self, user_params: dict) -> None:
        self.location: str = user_params['location']
        self.radius: float = user_params['radius']
        self.min_price: int = user_params['min_price']
        self.max_price: int = user_params['max_price']
        self.min_room: int = user_params['min_room']
        self.max_room: int = user_params['max_room']
        self.buy_rent: str = user_params['buy_rent']

    def get_location_id(self) -> str:
        tokenise_loc = "".join(char + ('/' if i % 2 == 1 else '') for i, char in enumerate(self.location.upper()))
        url = f"https://www.rightmove.co.uk/typeAhead/uknostreet/{tokenise_loc.strip('/')}/"
        response = requests.get(url)
        response_data = json.loads(response.text)

        return response_data["typeAheadLocations"][0]["locationIdentifier"]

    def get_url_params(self, offset: int) -> str:
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
    url = "https://www.rightmove.co.uk/api/_search?"
    params_url = search_request.get_url_params(offset)
    url += params_url
    return url

def get_properties(user_params) -> set:
    sr = SearchRequest(user_params)

    first_page = requests.get(build_url(sr, 0))
    first_page_data = json.loads(first_page.text)
    total_results = int(first_page_data["resultCount"].replace(',', ''))
    results = [p["id"] for p in first_page_data["properties"]]

    max_api_result = 1000
    for offset in range(RESULTS_PER_PAGE, total_results, RESULTS_PER_PAGE):
        if offset < max_api_result:
            page_response = requests.get(build_url(sr, offset))
            page_data = json.loads(page_response.text)
            results.extend([p["id"] for p in page_data["properties"]])

    return set(results)

def check_for_new_properties(latest_ppt_data: set) -> set:
    with open("property_data.pkl", "rb") as f:
        old_ppt_data = pickle.load(f)

    return latest_ppt_data.difference(old_ppt_data)

def create_property_urls(properties: set, max_amount: int) -> list:
    url_list = []
    for p in list(properties)[:max_amount]:
        url_list.append(f"https://www.rightmove.co.uk/properties/{p}#/")

    return url_list

def discord_post(url_list):
    webhook = SyncWebhook.from_url(os.getenv('DISCORD_WEBHOOK_URL'))
    for url in url_list:
        webhook.send("A new flat has been found!\n\n"+ url + "\n")
        print("Posted to discord\n")


def main():
    user_params = {
        "location": "Camden",
        "radius": 0.25,
        "min_price": 100,
        "max_price": 2500,
        "min_room": 1,
        "max_room": 2,
        "buy_rent": "RENT",
    }

    properties = get_properties(user_params)

    with open("property_data.pkl", "wb") as f:
        pickle.dump(properties, f)

    urls = create_property_urls(properties, 5)
    print(urls)
    discord_post(urls)


if __name__ == "__main__":
    main()