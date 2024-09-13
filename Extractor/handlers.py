import logging
import requests

class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhookUrl):
        super().__init__()
        self.webhookUrl = webhookUrl
    
    def emit(self, record):
        entry = self.format(record)

        response = requests.post(url=self.webhookUrl, json={"content": entry})
        if response.status_code != 204:
            print(f"Send log to discord failure: {response.status_code}")