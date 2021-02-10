import time

from pynput.keyboard import Key, Controller
from selenium import webdriver
from selenium.webdriver.common.by import By
from lib_config import Config

from .browser import Browser


class ConvenienceBrowser(Browser):
    """Browser with funcs for random websites"""

    def __init__(self, *args, **kwargs):
        super(ConvenienceBrowser, self).__init__(*args, **kwargs)
        self.set_discord_init_attrs()
        self.set_blackboard_init_attrs()
        self.set_ice_man_init_attrs()

    def close(self, *args, **kwargs):
        super(ConvenienceBrowser, self).close(*args, **kwargs)
        self.set_discord_close_attrs()
        self.set_blackboard_close_attrs()
        self.set_ice_man_init_attrs()

#####################
### Discord Funcs ###
#####################

    def set_discord_init_attrs(self):
        self.discord_logged_in = False

    def open_channel(self, channel, open_new=True):
        if open_new:
            self.open()
        self.get(f"https://discord.com/channels/{channel}")
        if open_new or self.discord_logged_in is False:
            self.discord_login()

    def discord_login(self):
        email, password = Config().discord_creds()
        self.wait_send_keys(name="email", keys=email)
        self.wait_send_keys(name="password", keys=password)
        self.wait_click(xpath="//button[@type='submit']")
        self.discord_logged_in = True

    def set_discord_close_attrs(self):
        self.discord_logged_in = False

########################
### Blackboard Funcs ###
########################

    def set_blackboard_init_attrs(self):
        self.blackboard_logged_in = False

    def open_blackboard(self, open_new=True):
        if open_new:
            self.open()
        self.get(f"https://lms.uconn.edu/")
        if open_new or self.blackboard_logged_in is False:
            self.blackboard_login()
        # Wait for load, then jump to courses
        while "institution-page" not in self.url:
            time.sleep(.1)
        self.get("https://lms.uconn.edu/ultra/course")

    def blackboard_login(self):
        netid, password = Config().blackboard_creds()
        # Remove popup
        self.wait_click(_id="agree_button")
        # Click login
        self.wait_click(_id="cas-login")
        self.wait_send_keys(_id="username", keys=netid)
        self.wait_send_keys(_id="password", keys=password)
        self.wait_click(name="submit")
        self.blackboard_logged_in = True

    def set_blackboard_close_attrs(self):
        self.blackboard_logged_in = False

##################
### Math funcs ###
##################

    def open_math_website(self, open_new=True):
        if open_new:
            self.open()
        self.get("http://www2.math.uconn.edu/"
                 "~olshevsky/classes/2021_Spring/math2210/math2210.php")
        self.math_login()

    def math_login(self):
        username, password = ["math2210", "Gauss"]
        self.wait_send_keys(name="txtUsername", keys=username)
        self.wait_send_keys(name="txtPassword", keys=password)
        self.wait_click(xpath="//input[@type='submit']")

#####################
### Ice Man Funcs ###
#####################

    def set_ice_man_init_attrs(self):
        self.ice_man_logged_in = False

    def open_ice_man(self, open_new=False):
        if open_new:
            self.open()
        self.get("https://www.wimhofmethod.com/login")
        if open_new or self.ice_man_logged_in is False:
            self.ice_man_login()
        # Wait for load, then jump to courses
        while "https://www.wimhofmethod.com/members/dashboard" not in self.url:
            time.sleep(.1)
        self.get("https://www.wimhofmethod.com/elearning/10-week-video-course")
        self.wait_click(xpath="//*[text()=' Continue ']")
        time.sleep(1)
        self.center_click()

    def center_click(self):
        size = self.browser.get_window_size()
        action = webdriver.common.action_chains.ActionChains(self.browser)
        action.move_to_element_with_offset(self.get_el(tag="body"),
                                           size["width"] // 2,
                                           size["height"] // 2)
        action.click()
        action.perform()

    def ice_man_login(self):
        email, password = Config().ice_man_creds()
        time.sleep(1)
        # Removes popup
        self.type_keys([Key.tab, Key.enter])
        self.wait_send_keys(name="email", keys=email)
        self.wait_send_keys(name="password", keys=password)
        self.wait_click(xpath="//input[@type='submit']")
        self.ice_man_logged_in = True

    def set_ice_man_close_attrs(self):
        self.ice_man_logged_in = False
