from lib_config import Config

from .browser import Browser

class Discord_Browser(Browser):
    def open_channel(self, channel):
        self.open()
        self.get(f"https://discord.com/channels/{channel}")
        email, password = Config().discord_creds()
        self.wait_send_keys(name="email", keys=email)
        self.wait_send_keys(name="password", keys=password)
        self.wait_click(xpath="//button[@type='submit']")
