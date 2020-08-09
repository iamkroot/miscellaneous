from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import time
from solve_captcha import solve_captcha
from config import DOB, APPL_NO, STATE_CODE

BASE_URL = "https://sarathi.parivahan.gov.in/"


img_script = """
let c = document.createElement('canvas');
let ctx = c.getContext('2d');
let img = document.getElementById('captchaImg');
c.height=img.naturalHeight;
c.width=img.naturalWidth;
ctx.drawImage(img, 0, 0,img.naturalWidth, img.naturalHeight);
return c.toDataURL();
"""
browser = webdriver.Firefox()
browser.get(BASE_URL)
browser.implicitly_wait(30)
state_sel = Select(browser.find_element_by_id("stfNameId"))
state_sel.select_by_value(STATE_CODE)
css = browser.find_element_by_css_selector
by_id = browser.find_element_by_id
# slot booking item
css("li.active:nth-child(3) > a:nth-child(1)").click()

# drivers skill
css("li.active:nth-child(3) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)").click()


def fill_dl_appl_details():
    # dlslotbook
    time.sleep(5)
    browser.execute_script('document.querySelector("li.dropdown:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)").click()')
    # application number
    appl_radio = by_id("dlslotipform_subtype1")
    actions = ActionChains(browser)
    actions.move_to_element(appl_radio)
    actions.click()
    actions.perform()

    by_id("applno").send_keys(APPL_NO)
    by_id("dob").send_keys(DOB)
    by_id("applno").click()

    captcha = browser.execute_script(img_script)
    captcha_text = solve_captcha(captcha)
    print(captcha_text)
    by_id("captcha").send_keys(captcha_text)
    by_id("dlslotipform_   SAVE   ").click()


for i in range(10):
    fill_dl_appl_details()
    if "captcha" in by_id("msgbody").text.lower():
        by_id("btnOk").click()
    else:
        break
else:
    print("couldn't solve captcha")
    exit()

by_id("1").click()
by_id("prcdbook").click()
try:
    css("#dispdlapcntdetform > div:nth-child(1) > h3:nth-child(7)")
except NoSuchElementException:
    print("Available")
else:
    print("Not available")
