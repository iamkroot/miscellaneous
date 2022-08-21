from pathlib import Path
import re
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import TimeoutException

DIR = Path("/home/kroot/Pictures/New Walls/")
files = list(DIR.iterdir())
files.sort()

pat = re.compile(r"wallhaven-(?P<id>[0-9a-z]+)")
URL = "https://wallhaven.cc/w/"
opt = Options()
opt.add_argument("--user-data-dir=/home/kroot/.config/google-chrome/")
# driver = WebDriver(options=opt)


def fav(wall_id: str):
    url = URL + wall_id
    driver.get(url)

    not_found, found, alread_fav = False, False, False

    def load_cond(driver: WebDriver):
        nonlocal not_found, found, alread_fav
        not_found = "not found" in driver.title 
        try:
            found = driver.find_element(By.CLASS_NAME, "add-fav")
        except NoSuchElementException:
            found = False
        try:
            alread_fav = driver.find_element(By.CLASS_NAME, "in-favorites")
        except NoSuchElementException:
            alread_fav = False
        return not_found and found and alread_fav
    try:
        WebDriverWait(driver, 5).until_not(load_cond)
    except TimeoutException:
        print("No condition met", wall_id)
        return
    if not_found:
        print("No wallpaper found", wall_id)
        return
    elif alread_fav:
        print("Wall already in favorites", wall_id)
        return
    elif found is False or found is None:
        print("No condition met")
        title = driver.title
        raise Exception(f"Unknown error {title}")
    found.click()
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "in-favorites"))
        )
    except TimeoutException:
        print("Failed to add to favorites", wall_id)
    else:
        print("Added to favorites", wall_id)


count = 0
old = 0
for file in files:
    m = pat.search(file.stem)
    if not m:
        continue
    wall_id = m['id']
    count += 1
    # if wall_id < "q2rj1r":
    #     print("skipping", wall_id)
    #     continue
    try:
        int(wall_id)
    except ValueError:
        pass
    else:
        old += 1
        print("skipping old id", wall_id)
        continue
    print(wall_id)
    # fav(wall_id)

print(count, old)