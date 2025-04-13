from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def explore_page(driver: webdriver.Chrome, url: str) -> list[str]:
    driver.get(url)
    time.sleep(2)  # Allow the page to load initially
    
    landing_page_urls = set()
    
    # Assuming we are looking for elements that contain the links to landing pages
    while True:
        # Extract the landing page links
        links = driver.find_elements(By.CSS_SELECTOR, 'a.fp_yearbtn')
        for link in links:
            landing_page_urls.add(link.get_attribute('href'))
        
        # Try to find a 'load more' button or next page button, scroll down if needed
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Load more') or contains(text(),'Mehr')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
            load_more_button.click()
            time.sleep(2)  # Wait for new content to load
        except:
            break  # No more buttons found, exit the loop
    
    return list(landing_page_urls)