from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.constants import DAY_OF_WEEK
from classes.supermarket import Supermarket, WorkingHour
import time

#Wait until not working when multiple elements with same selectors, had to implement time.sleep()

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

def get_market_data(browser, supermarket):
    wait = WebDriverWait(browser, 10)
    
    #General info
    supermarket.name = browser.find_element(By.XPATH, '//h1[@class="market-header__title"]').get_attribute("innerHTML")
    
    #'Sobre' tab information
    browser.find_element(By.XPATH, '//button[@class="information-details-button"]').click()
    info_element = browser.find_elements(By.XPATH, '//p[@class="merchant-details-about__info-data"]')
    supermarket.address = info_element[0].get_attribute("innerHTML") +', ' + info_element[1].get_attribute("innerHTML")
    supermarket.zip_code = info_element[2].get_attribute("innerHTML").split('CEP: ')[1]
    supermarket.cnpj = info_element[3].get_attribute("innerHTML").split('CNPJ: ')[1]
    
    #'Horário' tab information
    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="marmita-tab1-1"]'))).click()
    working_hours = browser.find_elements(By.XPATH, '//span[contains(@class, "merchant-details-schedule__day-schedule")]')
    for index, hours in enumerate(working_hours):
        hours = hours.get_attribute("innerHTML").split(' às ')
        if(len(hours) == 2):
            setattr(supermarket.working_hours, DAY_OF_WEEK[index], WorkingHour(hours[0], hours[1]))
        elif(hours[0] == 'Não abre'):
            setattr(supermarket.working_hours, DAY_OF_WEEK[index], None)
    
    #Get delivery info
    browser.find_element(By.XPATH, '//span[@class="icon-marmita icon-marmita--close btn__icon"]').click()
    browser.find_element(By.XPATH, '//button[@class="delivery-button"]').click()
    #Get delivery days
    deliveryDays = browser.find_elements(By.XPATH, '//span[@class="day-small-card__number"]')
    deliveryDays[0].click()
    deliveryDaysValues = []
    for deliveryDay in deliveryDays:
        deliveryDaysValues.append(deliveryDay.get_attribute("innerHTML"))
    supermarket.delivery_days = deliveryDaysValues
    supermarket.delivery_price = browser.find_element(By.XPATH, '//span[@class="delivery-card__price"]').get_attribute("innerHTML")
    #If there is no disabled element then there is a option to grab the delivery
    try:   
        browser.find_element(By.XPATH, '//label[@class="selectable-input-card-container selectable-input-card-container--disabled"]')
        supermarket.grab_delivery = False
    except:
        supermarket.grab_delivery = True
    return supermarket

def get_products(browser, supermarket):
    return {}
    

def ifood_market_scrape():
    browser = webdriver.Chrome()
    browser.get('https://www.ifood.com.br/mercados')
    
    set_location(browser, 'Ermelino Matarazzo')
    urls = get_supermarket_pages(browser)
    failed_supermarkets = []
    
    for supermarket_url in urls:
        browser.get(supermarket_url)
        time.sleep(0.5)
        supermarket = Supermarket(supermarket_url)
        supermarket.url = supermarket_url
        try:
            get_market_data(browser,supermarket)
        except Exception as e:
            failed_supermarkets.append(supermarket_url)
            print("An error occurred while getting data from: ", supermarket_url)
            print(str(e))
        supermarket.display_info()     
        products = get_products(browser, supermarket)
        
    
    
    #Montar interface pra conseguir mais
    #