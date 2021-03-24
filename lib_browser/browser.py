import logging
from os.path import expanduser
import os
import subprocess
import time

from pynput.keyboard import Key, Controller
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import ChromeOptions as Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import JavascriptException
from selenium.common.exceptions import NoSuchElementException

# Loggers for selenium and url lib, which we do not want
from selenium.webdriver.remote.remote_connection import LOGGER
from urllib3.connectionpool import log as urllibLogger

from lib_utils.file_funcs import delete_paths
from lib_utils.helper_funcs import run_cmds, retry
from lib_utils.print_funcs import print_err

from .helpers import switch_to_window
from .side import Side

# Loggers for selenium and url lib, which we do not want
LOGGER.setLevel(logging.CRITICAL)
urllibLogger.setLevel(logging.WARNING)


class Browser:
    driver_path = os.path.join(expanduser("~"), "/tmp/chromedriver")

    def __init__(self,
                 side=Side.LEFT,
                 default_iframe=True):
        if not os.path.exists(self.driver_path):
            self.install()

        self.pdf = False
        self.default_iframe = default_iframe
        self.side = side
        self.keyboard = Controller()

    def install(self):
        """Installs chromedriver to driverpath"""

        self._install_google_chrome()
        self._install_chromedriver()

    @property
    def url(self):
        return self.browser.current_url

    def open(self):
        self.browser = webdriver.Chrome(executable_path=self.driver_path,
                                        chrome_options=self._get_chrome_opts())

    def close(self):
        self.browser.close()
        self.browser.quit()

    def maximize(self):
        self.browser.maximize_window()

    def get(self, url):
        self.browser.get(url)

    def back(self):
        self.browser.back()

    def scroll_up(self):
        self._scroll(Key.up)

    def scroll_down(self):
        self._scroll(Key.down)

    def page_up(self):
        self._scroll(Key.page_up)

    def page_down(self):
        self._scroll(Key.page_down)

    @switch_to_window()
    def open_new_tab(self, url=""):
        self.browser.execute_script(f"window.open('{url}');")

    # https://stackoverflow.com/a/51893230/8903959
    @print_err(Exception)
    def tab_over(self):
        handles = self.browser.window_handles
        if len(self.browser.window_handles) >= 2:
            current_handle = self.browser.current_window_handle
            i = handles.index(current_handle)
            switch_index = 0 if i + 1 >= len(handles) else i + 1
            self.browser.switch_to.window(handles[switch_index])

    def refocus(self):
        handle = self.browser.current_window_handle
        self.open_new_tab()
        self.browser.close()
        self.browser.switch_to.window(handle)
        self.switch_to_iframe()
        self._attempt_to_click()

    def type_keys(self, keys: list):
        for key in keys:
            self.keyboard.press(key)
            self.keyboard.release(key)
            time.sleep(.25)

    def accept_pop_up(self):
        try:
            self.browser.switch_to.alert.accept()
        except Exception:
            self.type_keys([Key.enter])
        self.switch_to_iframe()

    def show_links(self, open_new=False):
        if open_new:
            self.open()
        if self.default_iframe:
            self.switch_to_iframe()
        self._remove_numbers()
        self._show_numbers()

    def switch_to_iframe(self):
        self.browser.switch_to.default_content()
        iframe_name = self._get_iframe_name()
        if iframe_name:
            # Everything from here on in operates from within an iframe
            # Wait for iframe to load
            frame = self.wait(iframe_name, By.NAME)
            # Switch to iframe, life is good
            self.browser.switch_to.frame(frame)
            # Switch to inner frame if available
            inner_frame = self.get_el(tag="iframe")
            if inner_frame:
                self.browser.switch_to.frame(inner_frame)
        # unfortuately some iframes are worthless so do not include

    @print_err(JavascriptException)
    @switch_to_window()
    def click_number(self, num):
        num_str = self._format_number(num)
        self.switch_to_iframe()
        javascript = (f"document.getElementById('{self.num_attr}_{num_str}')"
                      ".nextSibling.click();")
        logging.info(javascript)
        self.browser.execute_script(javascript)

    @print_err(Exception, "Failed to click latest download: {}")
    @switch_to_window()
    def click_latest_download(self, retry=True):
        og_source = self.browser.page_source
        self.get("chrome://downloads/")
        time.sleep(1)
        self.type_keys([Key.tab, Key.tab, Key.enter])
        if og_source == self.browser.page_source and retry:
            self._attempt_to_click()
            self.click_latest_download(retry=False)

    @print_err(NoSuchElementException, "Can't find el: {}")
    def get_el(self,
               _id=None,
               name=None,
               tag=None,
               xpath=None,
               aria_label=None,
               plural=False):
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
        elif aria_label:
            css = f"[aria-label='{aria_label}']"
            if plural:
                return self.browser.find_elements_by_css_selector(css)
            else:
                return self.browser.find_element_by_css_selector(css)

        # SEE FUNC. DO NOT DELETE
        # self.get_el_new()

    def valid_elem(self, elem):
        return True if elem.is_displayed() and elem.is_enabled() else False

    def right_click_tag(self, tag):
        elem = self.wait(tag, By.TAG)
        ActionChains(self.browser).context_click(elem).perform()

    def wait(self, identifier, _type):

        wait = WebDriverWait(self.browser, 10)
        return wait.until(EC.element_to_be_clickable((_type, identifier)))

    def wait_click(self, _id=None, name=None, xpath=None, tag=None, _class=None):
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
            _type = By.TAG_NAME
            identifier = tag
        elif _class:
            _type = By.CLASS_NAME
            identifier = _class
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

    def remove_elements_by_tag(self, tag):
        # https://stackoverflow.com/a/14003629/8903959
        javascript = ("var element = "
                      f"document.getElementsByTagName('{tag}'), index;"
                      "for (index = element.length - 1; index >= 0; index--) {"
                      "element[index].parentNode.removeChild(element[index]);"
                      "}")
        self.browser.execute_script(javascript)

####################
### Helper Funcs ###
####################

    def _get_iframe_name(self):

        iframe_links = {"https://lms.uconn.edu/ultra/courses":
                        "classic-learn-iframe",
                        "https://class.mimir.io/projects/":
                            "main.pdf",
                        }

        # https://stackoverflow.com/a/24286392
        for iframe_link, iframe_name in iframe_links.items():
            if iframe_link in self.url:
                return iframe_name

############################
### Install Helper Funcs ###
############################

    def _install_google_chrome(self):
        run_cmds("sudo apt-get update -y")
        run_cmds("sudo apt-get upgrade -y")

        chrome_install_base = "/tmp"
        chrome_install_name = "google-chrome-stable_current_amd64.deb"
        chrome_install_path = os.path.join(chrome_install_base,
                                           chrome_install_name)

        if os.path.exists(chrome_install_path):
            delete_paths(chrome_install_path)

        run_cmds([f"cd {chrome_install_base}",
                  ("wget https://dl.google.com/linux/direct/"
                   f"{chrome_install_name}"),
                  f"sudo apt install ./{chrome_install_name}"])

    def _install_chromedriver(self):
        path = '/'.join(self.driver_path.split('/')[:-1])

        if os.path.exists(self.driver_path):
            delete_paths(self.driver_path)

        # Installs chromedriver
        # https://gist.github.com/mikesmullin/2636776#gistcomment-2608206
        cmd = ("LATEST_VERSION=$(curl -s "
               "https://chromedriver.storage.googleapis.com/LATEST_RELEASE) &&"
               " wget -O /tmp/chromedriver.zip "
               "https://chromedriver.storage.googleapis.com/$LATEST_VERSION/"
               "chromedriver_linux64.zip && "
               "unzip /tmp/chromedriver.zip "
               f"chromedriver -d {path};")
        run_cmds(cmd)

################################
### Opening Helper Functions ###
################################

    def _get_chrome_opts(self):
        width, height = self._get_dims()
        if self.side in [Side.LEFT, Side.RIGHT]:
            width = width // 2
        # Get chrome options
        opts = Options()
        # https://stackoverflow.com/a/37151037/8903959
        opts.add_argument(f"--window-size={width},{int(height * .9) }")
        # Set new position
        if self.side in [Side.LEFT, Side.CENTER]:
            opts.add_argument("--window-position=0,0")
        elif self.side == Side.RIGHT:
            opts.add_argument(f"--window-position={width + 1},0")
        else:
            assert False, "Not implimented, side is not left/right/center"

        return opts

    def _get_dims(self):
        """Gets width and height of monitor"""

        # https://stackoverflow.com/a/3598320/8903959
        # Made this a raw string to avoid invalid esc char
        output = subprocess.Popen(r'xrandr | grep "\*" | cut -d" " -f4',
                                  shell=True,
                                  stdout=subprocess.PIPE).communicate()[0]
        outputs = [x for x in output.decode('utf-8').split("\n") if x]
        if len(outputs) == 1:
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
            assert False, f"Couldn't get dimensions, >2 monitors?: {outputs}"

###########################
### Scroll Helper Funcs ###
###########################

    def _scroll(self, key):
        if "pdf" not in self.url and "chrome://downloads/" not in self.url:
            self._javascript_scroll(key)
        elif "pdf" in self.url or "chrome://downloads/" in self.url:
            self._type_scroll(key)

    def _javascript_scroll(self, key, retry=True):
        move_dict = {Key.down: 200,
                     Key.up: -200,
                     Key.page_down: 500,
                     Key.page_up: -500}
        logging.debug("Executing window javascript scroll")
        _javascript = "window.scroll({top:"
        _javascript += f"window.pageYOffset + {move_dict[key]}"
        _javascript += ",left:0,behavior: 'smooth'})"
        self.browser.execute_script(_javascript)

    def _type_scroll(self, key):
        logging.debug("Trying type scroll")
        self._attempt_to_click()
        self.type_keys([key] * 6)

##################################
### Attempt Click Helper Funcs ###
##################################

    @print_err(MoveTargetOutOfBoundsException, "Out of bounds, click fail {}")
    def _attempt_to_click(self):
        try:
            self._click_body()
        except MoveTargetOutOfBoundsException:
            try:
                self._click_iframe()
            except MoveTargetOutOfBoundsException:
                self._click_browser()

    def _click_body(self):
        el = self.get_el(tag="body")
        action = ActionChains(self.browser)
        action = action.move_to_element_with_offset(el, 5, 5)
        self._action_click(action)

    def _click_iframe(self):
        el = self.get_el(tag="iframe")
        if el is None:
            raise MoveTargetOutOfBoundsException
        action = ActionChains(self.browser)
        action = action.move_to_element_with_offset(el, 5, 5)
        self._action_click(action)

    def _click_browser(self):
        width = self.browser.get_window_size()["height"]
        height = self.browser.get_window_size()["width"]
        action = ActionChains(self.browser)
        action = action.move_by_offset(width // 2, height // 2)
        self._action_click(action)

    def _action_click(self, action, clicks=3):
        for i in range(clicks):
            action = action.click()
        action.perform()

##########################
### Show Links Helpers ###
##########################

    def _remove_numbers(self):
        javascript = (f"var ele = "
                      f"document.getElementsByName('{self.num_attr}');"
                      "for(var i=ele.length-1;i>=0;i--)"
                      "{ele[i].parentNode.removeChild(ele[i]);}")
        self.browser.execute_script(javascript)

    @retry(JavascriptException, tries=2, msg="Javascript err: {}", sleep=1)
    def _show_numbers(self):
        javascript_strs = []
        elems = []
        clickables = self._get_clickables()
        # Don't include these numbers, too similar to other words
        # Or they precede other words (ex: twenty one)
        # If they precede and we search for 20 and 21, and they say 21,
        # We would select 20 before waiting to hear the one
        nums_to_exclude = set([1, 2, 4, 6, 7, 8, 9, 10, 11, 13,
                               14, 20, 30, 40, 50, 60, 70, 80, 90,
                               21, 31, 41, 51, 61, 71, 81, 91,
                               22, 32, 42, 52, 62, 72, 82, 92,
                               24, 34, 44, 54, 64, 74, 84, 94])
        # Remove the nums to exclude
        nums_to_use = [x for x in
                       range(len(clickables) + len(nums_to_exclude))
                       if x not in nums_to_exclude]
        if len(clickables) >= 100:
            logging.warning("Only can click up to 99, sorry")
        # Labeling of clickables
        for label_num, (i, el) in zip(nums_to_use, enumerate(clickables)):
            javascript_str, new_elem = self._add_number_to_el(label_num, i, el)
            javascript_strs.append(javascript_str)
            elems.append(new_elem)
        # Done all at once for speed
        self.browser.execute_script(" ".join(javascript_strs), *elems)
        logging.debug("Done showing adding numbers")

    # Retries func a few times to acct for load times
    @retry(err=StaleElementReferenceException, msg="clickables not found")
    def _get_clickables(self):
        a_tags = self.get_el(tag="a", plural=True)
        # https://stackoverflow.com/a/48365300/8903959
        submit_buttons = self.get_el(xpath="//input[@type='submit']",
                                     plural=True)
        input_buttons = self.get_el(xpath="//input[@type='button']",
                                    plural=True)

        other_buttons = self.get_el(tag="button", plural=True)

        buttons = submit_buttons + other_buttons + input_buttons

        standard_buttons = [x for x in buttons
                            if (x.get_attribute("value")
                                # Get rid of weird button google search page
                                and "Lucky" not in x.get_attribute("value")
                                ) or not x.get_attribute("value")]

        radio_buttons = self.get_el(xpath="//input[@type='radio']",
                                    plural=True)

        clickables = a_tags + standard_buttons + radio_buttons
        return [elem for elem in clickables if self.valid_elem(elem)]

    def _add_number_to_el(self, label_num, true_num, elem):
        # https://stackoverflow.com/a/18079918
        num_str = self._format_number(label_num)

        # https://www.quora.com/how-do-i-add-an-html-element-using-selenium-webdriver
        javascript_str = (f"var iii = document.createElement('i');"
                          f"var text = document.createTextNode('{num_str}');"
                          "iii.appendChild(text);"
                          f"iii.id = '{self.num_attr}_{num_str}';"
                          f"iii.setAttribute('name','{self.num_attr}');"
                          "iii.style.color='white';"
                          "iii.style.backgroundColor='black';"
                          "iii.style.order=100;"
                          f"arguments[{true_num}].before(iii);")
        return javascript_str, elem

    def _format_number(self, num):
        return f"__{num}__"

    @property
    def num_attr(self):
        return "furuness"

##########################
### Legacy Funcs/Other ###
##########################

    def get_el_new(self):
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

    def _send_keys_to_body_scroll(self, key, page):
        assert False, "legacy func, no longer used"
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
