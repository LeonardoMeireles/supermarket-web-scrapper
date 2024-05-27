from src.ifood.scrapper import ifood_market_scrape  # pragma: no cover
from src.database.database import connect_market_db
from dotenv import load_dotenv, find_dotenv
from mapbox import Geocoder
import os

if __name__ == "__main__":  # pragma: no cover
    load_dotenv(find_dotenv())
    conn = connect_market_db()
    geocoder = Geocoder(access_token=os.environ['MAPBOX_ACCESS_TOKEN'])
    
    ifood_market_scrape(conn, geocoder)
    conn.close()