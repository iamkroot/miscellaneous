#! /home/kroot/.virtualenvs/scrape/bin/python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

from pathlib import Path
import json

# List of leetcode problem urls
problem_urls = json.loads(Path("problems.txt").read_text())

done_path = Path("lcdone.txt")
done = json.loads(done_path.read_text() or "[]" if done_path.exists() else "[]")
done = []

# Set up the webdriver
firefox_profile_path = 'XXXX'
firefox_options = Options()
firefox_options.profile = firefox_profile_path

# Launch Firefox with existing profile
driver = webdriver.Firefox(options=firefox_options)

# Navigate to the login page
driver.get("https://leetcode.com/accounts/login/")
# FIXME: Verify that user is already logged in
time.sleep(2)

LIST_NAME = "XXXX"

wait = WebDriverWait(driver, 10)

def work_url(url):
    driver.get(url)
    # Here you can add your logic to extract information from the problem page
    # "div[id^='headlessui-popover-button-'"
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='headlessui-popover-button-']")))
    buts = driver.find_elements(By.CSS_SELECTOR, "div[id^='headlessui-popover-button-']")
    listbut = buts[1]
    print(listbut, listbut.get_attribute('innerHTML'))
    listbut.click()
    time.sleep(0.5)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='headlessui-popover-panel-'] a[href='/list/']")))
    panel = driver.find_element(By.CSS_SELECTOR, "div[id^='headlessui-popover-panel-']")
    time.sleep(0.5)
    try:
        add_but = panel.find_element(By.XPATH, f"//span[contains(text(), '{LIST_NAME}')]/../../../div[contains(text(), 'Add')]")
    except NoSuchElementException:
        # will raise exception if not found
        panel.find_element(By.XPATH, f"//span[contains(text(), '{LIST_NAME}')]/../../../div[contains(text(), 'Remove')]")
        print(url, "already added to list")
        done.append(url)
        time.sleep(2)
        return

    add_but.click()


def func():
    # Loop through each url and open it in the browser
    for url in problem_urls:
        if url in done:
            print("already done", url)
            continue
        try:
            work_url(url)
        except TimeoutException:
            # FIXME: Should detect premium properly
            print("probably premium", url)
        done.append(url)
        time.sleep(2)

def main():
    try:
        func()
    finally:
        done_path.write_text(json.dumps(done))
    # Close the browser
    driver.quit()


main()
