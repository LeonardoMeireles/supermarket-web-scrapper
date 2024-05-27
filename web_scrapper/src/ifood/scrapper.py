from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.constants import DAY_OF_WEEK
from classes.supermarket import Supermarket, WorkingHour, Product
from src.database.database import *
from datetime import datetime, timedelta
import requests
import time

#TODO: Try adding Selenium wait on elements, couldn't get it to work

def set_location(browser, address):
    wait = WebDriverWait(browser, 10)
    #Input address in input
    wait.until(EC.presence_of_element_located((By.XPATH, '//button[@class="address-search-input__button"]'))).click()
    browser.find_elements(By.XPATH, '//input[@class="address-search-input__field"]')[1].send_keys(address)
    
    #Select first option from dropdown of addresses
    time.sleep(1.7)
    browser.find_elements(By.XPATH, '//button[@class="btn-address--full-size"]')[1].click()
    
    #Confirm and save address
    try :
        wait.until(EC.presence_of_element_located((By.XPATH, '//button[@class="btn btn--default btn--size-m address-maps__submit"]'))).click()
    except:
        browser.find_element(By.XPATH, '//button[@class="btn btn--link btn--size-m marmita-error-message__try-again"]').click()
        time.sleep(1.7)
        browser.find_elements(By.XPATH, '//button[@class="btn-address--full-size"]')[1].click()
        wait.until(EC.presence_of_element_located((By.XPATH, '//button[@class="btn btn--default btn--size-m address-maps__submit"]'))).click()
    time.sleep(0.5)
    browser.find_elements(By.XPATH, '//button[@class="btn btn--default btn--size-m btn--full-width"]')[0].click()

def get_supermarket_pages(browser):
    wait = WebDriverWait(browser, 10)
    #Go to list of supermarkets page
    wait.until(EC.presence_of_element_located((By.XPATH, '//span[text()="Super Mercados"]'))).click()
    time.sleep(1)
    #Get url of every supermarket page
    list_supermarket = browser.find_elements(By.XPATH, '//a[@class="merchant-v2__link"]')
    return [supermarket.get_attribute('href') for supermarket in list_supermarket]

def get_market_data_api(supermarket): 
    ifood_market_id = supermarket.url.split('/')[-1]
    #TODO: Delivery price is based on latitude and longitude of user, find a way to get all delivery prices by distance
    #Will set a default location to get the takeout option
    latitude = -23.4866078
    longitude = -46.5138969
    url = f'https://marketplace.ifood.com.br/v1/merchant-info/graphql?latitude={latitude}&longitude={longitude}&channel=IFOOD'
    body = {
        "query": "query ($merchantId: String!) { merchant (merchantId: $merchantId, required: true) { deliveryFee { originalValue type value } deliveryMethods { catalogGroup deliveredBy id maxTime minTime mode originalValue priority schedule { now shifts { dayOfWeek endTime interval startTime } timeSlots { availableLoad date endDateTime endTime id isAvailable originalPrice price startDateTime startTime } } subtitle title type value state } id name } merchantExtra (merchantId: $merchantId, required: false) { address { city country district latitude longitude state streetName streetNumber timezone zipCode } description documents { CNPJ { type value } MCC { type value } } enabled id locale name phoneIf shifts { dayOfWeek duration start } } }",
        "variables": {
            "merchantId": ifood_market_id
        }
    }
    res = requests.post(url, json=body)
    if(res.status_code == 200):
        about_data = res.json()['data']['merchantExtra']
        supermarket.name = about_data['name']
        
        addreess_data = about_data['address']
        supermarket.address = f"{addreess_data['streetName'].capitalize()}, {addreess_data['streetNumber']} - {addreess_data['district'].capitalize()} - {addreess_data['city'].capitalize()} - {addreess_data['state'].upper()}"
        supermarket.zip_code = addreess_data['zipCode']
        supermarket.cnpj = about_data['documents']['CNPJ']['value']
        
        for day in DAY_OF_WEEK.values():
            ifood_day_data = next((obj for obj in about_data['shifts'] if obj.get("dayOfWeek").capitalize() == day), None)
            if(ifood_day_data is not None):
                start_time_obj = datetime.strptime(ifood_day_data['start'], '%H:%M:%S')
                close_time_obj = start_time_obj + timedelta(minutes=ifood_day_data['duration'])
                close_time = close_time_obj.strftime('%H:%M:%S')
                setattr(supermarket.working_hours, day, WorkingHour(ifood_day_data['start'], close_time))
            else:
                setattr(supermarket.working_hours, day, None)
        
        delivery_methods = res.json()['data']['merchant']['deliveryMethods']
        for method in delivery_methods:
            if method['mode'] == 'DELIVERY':
                supermarket.delivery_price = round(method['originalValue'], 2)
            elif method['mode'] == 'TAKEOUT':
                supermarket.takeout = True
            else:
                print('Unknown delivery mode: ', method.mode)
                
    elif (res.status_code == 429):
        print('Timeout happened')
        # From time to time we make too many requests, resulting in a 429 error code in the API
        # So we wait for the timeout to be done to continue making requests
        time.sleep(5)
        return get_market_data_api(supermarket)

def get_products_from_category(supermarket, market_id, category_id, page=1):
    more_products = True
    page_size = 600
    while more_products: 
            try:
                res = requests.get(f'https://marketplace.ifood.com.br/v1/merchants/{market_id}/catalog-category/{category_id}?items_page={page}&items_size={page_size}')
                if(res.status_code == 200):
                    res = res.json()
                    if('itens' in res['data']['categoryMenu']):
                        itens = res['data']['categoryMenu']['itens']
                        if(len(itens) < page_size):
                            more_products = False
                        for ifood_product in itens:
                            if('ean' not in ifood_product):
                                #TODO: treat combo promotions from Ifood (multiple items in one entity), could probably use embeding data.
                                continue
                            product = Product(ifood_product['description'], ifood_product['unitPrice'], ifood_product['ean'])
                            if('additionalInfo' in ifood_product):
                                product.description = ifood_product['additionalInfo']
                            supermarket.products.append(product)
                        page += 1
                    else:
                        #No more itens in category
                        more_products = False
                elif (res.status_code == 429):
                    print('Timeout happened')
                    # From time to time we make too many requests, resulting in a 429 error code in the API
                    # So we wait for the timeout to be done to continue making requests
                    time.sleep(5)
                    return get_products_from_category(supermarket, market_id, category_id, page)
            except Exception as e:
                print(e)
                print('Error on request:')
                print(f'https://marketplace.ifood.com.br/v1/merchants/{market_id}/catalog-category/{category_id}?items_page={page}&items_size={page_size}')
                
def get_products_api(supermarket):
    market_id = supermarket.url.split('/')[-1]
    res = requests.get(f'https://marketplace.ifood.com.br/v1/merchants/{market_id}/taxonomies')
    category_ids = [category_data["id"] for category_data in res.json()['data']['categories']]
    for category_id in category_ids:
        get_products_from_category(supermarket, market_id, category_id)

def setup_browser():
    browser = webdriver.Chrome()
    browser.get('https://www.ifood.com.br/mercados')
    #Sleep avoids getting blocked by website
    time.sleep(2)
    
    set_location(browser, 'Bairro Campestre')
    return browser

def scrape_market_by_url(supermarket_url, conn, geocoder):
    supermarket = Supermarket(supermarket_url)
    supermarket.url = supermarket_url
    get_market_data_api(supermarket)
    print(f'Got Market Data for {supermarket.name}')
    get_products_api(supermarket)
    if(len(supermarket.products) == 0):
        raise Exception("No product collected")
    save_to_db(supermarket, conn, geocoder)
    supermarket.display_info()
  
def ifood_market_scrape(connDefault, geocoder):
    conn = connDefault
    failed_supermarkets = []
    browser = setup_browser()
    urls = get_supermarket_pages(browser)
    browser.quit()

    #Test specific market
    # urls = ['https://www.ifood.com.br/delivery/guarulhos-sp/mercado-supernova-cidade-jardim-cumbica/d606edd4-c210-4f71-92f3-817c5a7670a6']

    for supermarket_url in urls:
        try:
            scrape_market_by_url(supermarket_url, conn, geocoder)
        except Exception as e:
            conn = connect_market_db()
            print("An error occurred while getting data from: ", supermarket_url)
            print(str(e))
            failed_supermarkets.append(supermarket_url)
    print('Num of failed supermarkets: ', len(failed_supermarkets))
    print('Failed Supermarkets: ', failed_supermarkets)
    