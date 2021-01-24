import time

from lib_config import Config

from .browser import Browser

class Convenience_Browser(Browser):
    """Browser with funcs for random websites"""

    def __init__(self, *args, **kwargs):
        super(Convenience_Browser, self).__init__(*args, **kwargs)
        self.set_discord_init_attrs()
        self.set_blackboard_init_attrs()

    def close(self, *args, **kwargs):
        super(Convenience_Browser, self).close(*args, **kwargs)
        self.set_discord_close_attrs()
        self.set_blackboard_close_attrs()

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
