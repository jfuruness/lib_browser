import sys
from enum import Enum
from os.path import expanduser
import os
import subprocess
import time

from pynput.keyboard import Key, Controller
import selenium
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver import ChromeOptions as Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from lib_utils import utils

from .side import Side

class Browser:
    driver_path = os.path.join(expanduser("~"), "/tmp/chromedriver")

    def __init__(self):
        if not os.path.exists(self.driver_path):
            self.install()
        self.in_iframe = False
        self.pdf = False

    @property
    def url(self):
        return self.browser.current_url

    def open(self, side=Side.LEFT):
        width, height = self._get_dims()
        if side in [Side.LEFT, Side.RIGHT]:
            width = width // 2
        # Get chrome options
        opts = Options()
        # https://stackoverflow.com/a/37151037/8903959
        opts.add_argument(f"--window-size={width},{int(height * .9) }")
        # Set new position
        if side in [Side.LEFT, Side.CENTER]:
            opts.add_argument("--window-position=0,0")
        elif side == Side.RIGHT:
            opts.add_argument(f"--window-position={new_width + 1},0")
        else:
            assert False, "Not implimented"
            
        self.browser = webdriver.Chrome(executable_path=self.driver_path,
                                        chrome_options=opts)
    def get(self, url):
        self.browser.get(url)

    def get_el(self, _id=None, name=None, tag=None, xpath=None, plural=False):
        try:
            if _id:
                return self.browser.find_element_by_id(_id)
            if name:
                return self.browser.find_element_by_name(name)
            if tag:
                if plural:
                    return self.browser.find_elements_by_tag_name(tag)
                else:
                    return self.browser.find_element_by_tag_name(tag)
            if xpath:
                if plural:
                    return self.browser.find_elements_by_xpath(xpath)
                else:
                    return self.browser.find_element_by_xpath(xpath)
        except Exception as e:
            print(str(_id) + str(name) + str(tag) + str(xpath))
            print(e)

        # DO NOT DELETE: This is the new version for selenium
        # However, it appears to have bugs
        # Bugs related to selenium that is, not in my code
        """
        if plural:
            find_func = self.browser.find_elements
        else:
            find_func = self.browser.find_element
        try:
            if _id:
                find_func(By.ID, _id)
            elif name:
                find_func(By.NAME, name)
            elif tag:
                find_func(By.TAG_NAME, tag)
            elif xpath:
                find_func(By.XPATH, xpath)
        except Exception as e:
            print(str(_id) + str(name) + str(tag) + str(xpath))
            print(e)
            raise e
        """

    def get_clickable(self, tries=5):
        try:
            a_tags = self.get_el(tag="a", plural=True)
            # https://stackoverflow.com/a/48365300/8903959
            submit_buttons = self.get_el(xpath="//input[@type='submit']", plural=True)
            other_buttons = self.get_el(xpath="//input[@type='button']", plural=True)
            standard_buttons = [x for x in submit_buttons + other_buttons
                                if (x.get_attribute("value")
                                    and "Lucky" not in x.get_attribute("value"))]
    
            radio_buttons = self.get_el(xpath="//input[@type='radio']", plural=True)
            clickables = a_tags + standard_buttons + radio_buttons
            
            return [elem for elem in clickables if self.valid_elem(elem)]
        # Sometimes in the middle of this elements dissapear so we must retry
        except selenium.common.exceptions.StaleElementReferenceException as e:
            if tries > 0:
                time.sleep(.1)
                return self.get_clickable(tries - 1)
            else:
                raise e

    def valid_elem(self, elem):
        if elem.is_displayed() and elem.is_enabled():
            return True
        else:
            return False

    def add_number(self, num, elem):
        # https://stackoverflow.com/a/18079918
        num_str = self._format_number(num)
        # https://www.quora.com/How-do-I-add-an-HTML-element-using-Selenium-WebDriver
        javascript_str = (f"var iii = document.createElement('i');"
                          f"var text = document.createTextNode('{num_str}');"
                          "iii.appendChild(text);"
                          f"iii.id = 'furuness_{num_str}';"
                          "iii.setAttribute('name','furuness');"
                          "iii.style.color='blue';"
                          "iii.style.backgroundColor='green';"
                          f"arguments[{num}].before(iii);")
        return (javascript_str, elem)

    def remove_number(self, num, elem):
        remove_str = self._format_number(num)
        num_str = elem.text.replace(remove_str, "")
        self.browser.execute_script(f"arguments[0].innerText = '{num_str}'",
                                    elem)
        if elem.get_attribute("type").lower() in ["submit", "button"]:
            num_str = elem.get_attribute("value").replace(remove_str, "")
            self.browser.execute_script(f"arguments[0].value = '{num_str}'",
                                        elem)

    def _format_number(self, num):
        return f"__{num}__"

    def _get_dims(self):
        """Gets width and height of monitor"""

    def _get_dims(self):
        """Gets width and height of monitor"""

        # https://stackoverflow.com/a/3598320/8903959
        output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',
                                  shell=True,
                                  stdout=subprocess.PIPE).communicate()[0]
        outputs = [x for x in output.decode('utf-8').split("\n") if x]
        if len(outputs) == 1:
            print(outputs)
            return [int(x) for x in outputs[0].split("x")]
        elif len(outputs) == 2:
            res1, res2 = outputs
            res1x, res1y = [int(x) for x in res1.split("x")]
            res2x, res2y = [int(x) for x in res2.split("x")]
            if res1x < res2x or res1y < res2y:
                return res2x, res2y
            else:
                return res1x, res1y
        else:
            assert False, f"Couldn't get dimensions: {outputs}"

    def install(self):
        """Installs chromedriver to driverpath"""

        # https://gist.github.com/mikesmullin/2636776#gistcomment-2608206
        cmd = ("LATEST_VERSION=$(curl -s "
               "https://chromedriver.storage.googleapis.com/LATEST_RELEASE) &&"
               " wget -O /tmp/chromedriver.zip "
               "https://chromedriver.storage.googleapis.com/$LATEST_VERSION/"
               "chromedriver_linux64.zip && "
               "unzip /tmp/chromedriver.zip "
               f"chromedriver -d {'/'.join(self.driver_path.split('/')[:-1])};")
        utils.run_cmds(cmd)

    def scroll_up(self):
        self.scroll("up")

    def refocus(self):
        handle = self.browser.current_window_handle
        self.open_new_tab()
        self.browser.close()
        self.browser.switch_to.window(handle)
        self.switch_to_iframe()
        self.attempt_to_click()

    def scroll_down(self):
        self.scroll("down")

    def scroll(self, key, page=False):
        if "pdf" not in self.url:
            print("trying javascript scroll")
            self.javascript_scroll(key, page)
            if "--test" in sys.argv:
                time.sleep(3)

        if "pdf" in self.url:
            # Must do twice
            self.attempt_to_click()
            print("Trying type scroll")
            self.type_scroll(key, page)
            if "--test" in sys.argv:
                time.sleep(3)

    def attempt_to_click(self):
        try:
            el = self.get_el(tag="body")
            action = webdriver.common.action_chains.ActionChains(self.browser)
            action = action.move_to_element_with_offset(el, 5, 5)

            action = action.click()
            action = action.click()
            action = action.click()
            action.perform()
        except selenium.common.exceptions.MoveTargetOutOfBoundsException:
            print("out of bounds, can't click for scroll")
            try:
                el = self.get_el(tag="iframe")
                if el is None:
                    raise selenium.common.exceptions.MoveTargetOutOfBoundsException
                action = webdriver.common.action_chains.ActionChains(self.browser)
                action = action.move_to_element_with_offset(el, 5, 5)

                action = action.click()
                action = action.click()
                action = action.click()
                action.perform()
            except:
                print("out of bounds, can't click for scroll")
                clicked = False
        try:
            width = self.browser.get_window_size()["height"]
            height = self.browser.get_window_size()["width"]
            action = webdriver.common.action_chains.ActionChains(self.browser)
            action = action.move_by_offset(width // 2, height // 2)

            action = action.click()
            action = action.click()
            action = action.click()
            action.perform()
        except selenium.common.exceptions.MoveTargetOutOfBoundsException:
            print("out of bounds")

    def javascript_scroll(self, key, page, retry=True):
        if key == "down":
            if page:
                move = 500
            else:
                move = 200
        elif key =="up":
            if page:
                move = -500
            else:
                move = -200
        print("Executing window javascript scroll")
        self.browser.execute_script("window.scroll({top:" + f"window.pageYOffset + {move}" + ",left:0,behavior: 'smooth'})")

    def send_keys_to_body_scroll(self, key, page):
        el = self.get_el(tag="body")
        for _ in range(6):
            if key == "down":
                if page:
                    send = Keys.PAGE_DOWN
                else:
                    send = Keys.ARROW_DOWN
            elif key == "up":
                if page:
                    send = Keys.PAGE_UP
                else:
                    send = Keys.ARROW_UP
            el.send_keys(send)

    def type_scroll(self, key, page):
        keyboard = Controller()
        if key=="down" and page:
            key_types = "page_down"
        elif key=="down":
            key_types = "down"
        elif key=="up" and page:
            key_types = "page_up"
        else:
            key_types = "up"
        for key_type in [key_types] * 6:
            keyboard.press(getattr(Key, key_type))
            keyboard.release(getattr(Key, key_type))
            time.sleep(.2)

    def page_up(self):
        self.scroll("up", page=True)

    def page_down(self):
        self.scroll("down", page=True)

    def right_click_tag(self, tag):
        elem = self.wait(tag, By.TAG)
        action = selenium.webdriver.ActionChains(self.browser)
        action.context_click(elem).perform()

    def wait(self, identifier, _type):

        wait = WebDriverWait(self.browser, 10)
        return wait.until(EC.element_to_be_clickable((_type, identifier)))

    def wait_click(self, _id=None, name=None, xpath=None, tag=None):
        if _id:
            _type = By.ID
            identifier = _id
        elif name:
            _type = By.NAME
            identifier = name
        elif xpath:
            _type = By.XPATH
            identifier = xpath
        elif tag:
            _type = By.TAG
            identifier = tag
        elem = self.wait(identifier, _type)
        elem.click()

    def wait_send_keys(self, _id=None, name=None, xpath=None, keys="a"):
        if _id:
            _type = By.ID
            identifier = _id
        elif name:
            _type = By.NAME
            identifier = name
        elif xpath:
            _type = By.XPATH
            identifier = xpath
        el = self.wait(identifier, _type)
        el.send_keys(keys)

    def open_new_tab(self, url=""):
        self.browser.execute_script(f"window.open('{url}');")
        self.browser.switch_to.window(self.browser.window_handles[-1])

    def switch_to_iframe(self, iframe=True):
        # Switches in and out of iframe
        if self.in_iframe:
            self.browser.switch_to.default_content()
            self.in_iframe = False
        if iframe is False:
            return

        iframe_links = {"https://lms.uconn.edu/ultra/courses":
                            "classic-learn-iframe",
#                        "https://class.mimir.io/projects/":
#                            "main.pdf"}
                        }

        # https://stackoverflow.com/a/24286392
        for iframe_link, iframe_name in iframe_links.items():
            if iframe_link in self.url:
                # Everything from here on in operates from within an iframe
                # Wait for iframe to load
                frame = self.wait(iframe_name, By.NAME)
                # Switch to iframe, life is good
                self.browser.switch_to.frame(frame)
            self.in_iframe = True
