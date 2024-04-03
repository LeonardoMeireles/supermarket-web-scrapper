from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def set_location(browser, address):
    wait = WebDriverWait(browser, 10)
    
    #Input address in input
    wait.until(EC.presence_of_element_located((By.XPATH, '//button[@class="address-search-input__button"]'))).click()
    time.sleep(0.5)
    browser.find_elements(By.XPATH, '//input[@class="address-search-input__field"]')[1].send_keys(address)
    
    #Select first option from dropdown of addresses
    time.sleep(2)
    browser.find_elements(By.XPATH, '//button[@class="btn-address--full-size"]')[1].click()
    
    #Confirm and save address
    time.sleep(1)
    browser.find_element(By.XPATH, '//button[@class="btn btn--default btn--size-m address-maps__submit"]').click()
    time.sleep(1)
    browser.find_elements(By.XPATH, '//button[@class="btn btn--default btn--size-m btn--full-width"]')[0].click()

def ifood_market_scrape():
    browser = webdriver.Chrome()
    browser.get('https://www.ifood.com.br/mercados')
    
    set_location(browser, 'Ermelino Matarazzo')