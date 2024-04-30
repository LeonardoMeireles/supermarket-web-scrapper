from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.constants import DAY_OF_WEEK
from classes.supermarket import WorkingHour, Product
from src.database.database import *
import time
import re


def getGeneralInfo(browser, supermarket):
    #General info
    supermarket.name = browser.find_element(By.XPATH, '//h1[@class="market-header__title"]').get_attribute("innerHTML")
    
    #'Sobre' tab information
    browser.find_element(By.XPATH, '//button[@class="information-details-button"]').click()
    info_element = browser.find_elements(By.XPATH, '//p[@class="merchant-details-about__info-data"]')
    supermarket.address = info_element[0].get_attribute("innerHTML") +', ' + info_element[1].get_attribute("innerHTML")
    zip_code = info_element[2].get_attribute("innerHTML").split('CEP: ')[1]
    supermarket.zip_code = re.sub('[^A-Za-z0-9]+', '', zip_code)
    cnpj = info_element[3].get_attribute("innerHTML").split('CNPJ: ')[1]
    supermarket.cnpj = re.sub('[^A-Za-z0-9]+', '', cnpj)

def getWorkingHours(browser, supermarket, wait):
    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="marmita-tab1-1"]'))).click()
    working_hours = browser.find_elements(By.XPATH, '//span[contains(@class, "merchant-details-schedule__day-schedule")]')
    for index, hours in enumerate(working_hours):
        hours = hours.get_attribute("innerHTML").split(' às ')
        if(len(hours) == 2):
            setattr(supermarket.working_hours, DAY_OF_WEEK[index], WorkingHour(hours[0], hours[1]))
        elif(hours[0] == 'Não abre'):
            setattr(supermarket.working_hours, DAY_OF_WEEK[index], None)
    browser.find_element(By.XPATH, '//span[@class="icon-marmita icon-marmita--close btn__icon"]').click()

def getDeliveryInfo(browser, supermarket, wait):
    browser.find_element(By.XPATH, '//button[@class="delivery-button"]').click()
    time.sleep(0.5)
    #Get delivery days
    deliveryDays = browser.find_elements(By.XPATH, '//span[@class="day-small-card__number"]')
    deliveryDays[0].click()
    supermarket.delivery_price = browser.find_element(By.XPATH, '//span[@class="delivery-card__price"]').get_attribute("innerHTML").split(' ')[1].replace(',','.')
    #If there is no disabled element then there is a option to grab the delivery
    try:   
        browser.find_element(By.XPATH, '//label[@class="selectable-input-card-container selectable-input-card-container--disabled"]')
        supermarket.takeout = False
    except:
        supermarket.takeout = True
    browser.find_element(By.XPATH, '//button[@class="delivery-scheduler-modal-close-button"]').click()

def get_market_data_headless(browser, supermarket): 
    wait = WebDriverWait(browser, 10)
    getGeneralInfo(browser, supermarket)
    getWorkingHours(browser, supermarket, wait)
    getDeliveryInfo(browser, supermarket, wait)
    return supermarket

def get_products_headless(browser, supermarket):
    productCategories = browser.find_elements(By.XPATH, '//li[@class="aisle-menu__item aisle-menu__item--without-taxonomies"]')
    for i in range(len(productCategories)):
        browser.execute_script("arguments[0].scrollIntoView(true);", productCategories[i]);
        browser.execute_script("window.scrollBy(0,-100)");
        try:
            productCategories[i].click()
        except:
            close_button = browser.find_element(By.XPATH, '//button[@class="delivery-scheduler-modal-close-button"]')
            close_button.click()
            productCategories[i].click()
        time.sleep(1)
        lastHeight = browser.execute_script('return document.body.scrollHeight')
        currentProductIndex = 0
        infiniteScrollActive = True
        while infiniteScrollActive:
            productContainers = browser.find_elements(By.XPATH, '//a[@class="product-card-content"]')
            productContainers = productContainers[currentProductIndex:]
            for pc in productContainers:
                name = pc.find_element(By.XPATH, './/span[@class="product-card__description"]').get_attribute("innerHTML")
                price = pc.find_element(By.XPATH, './/div[@class="product-card__price"]').get_attribute("innerHTML").split('R$ ')[1].replace(',','.')
                print(price, pc.find_element(By.XPATH, './/div[@class="product-card__price"]').get_attribute("innerHTML"))
                product = Product(name, price)
                try:
                    description = pc.find_element(By.XPATH, './/span[@class="product-card__details"]').get_attribute("innerHTML")
                    product.description = description
                except:
                    product.description = None
                currentProductIndex += 1
                supermarket.products.append(product)
                if(len(supermarket.products) > 20): 
                    return
            browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            #TODO: Improve by waiting for element with data-testid="three-dots-svg" to dissapear instead of sleep
            time.sleep(0.75)
            currentHeight = browser.execute_script('return document.body.scrollHeight')
            if(currentHeight != lastHeight):
                lastHeight = currentHeight
            else:
                infiniteScrollActive = False
    print('Finished getting products for ', supermarket.name)