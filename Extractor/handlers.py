import time
from datetime import datetime
import traceback
import logging
import requests

from discord import SyncWebhook, Embed, Colour

class ExtractorHandler(logging.Handler):
    def __init__(self, grafanaUrl: str, grafanaUserId: str, grafanaToken: str, discordUrl: str):
        super().__init__()
        self.grafanaUrl = grafanaUrl
        self.grafanaUserId = grafanaUserId
        self.grafanaToken = grafanaToken
        self.discordUrl = discordUrl
    
    def emit(self, record: logging.LogRecord):
        self._sendLoki(record=record)
        self._sendDiscord(record=record)

    def _sendLoki(self, record: logging.LogRecord):
        if record.exc_info:
            trace = traceback.format_exception(*record.exc_info)
            record.exc_info = None

        entry = self.format(record=record)

        logs = {
            "streams": [
                {
                    "stream": {
                        "service": "extractor",
                        "level": record.levelname.lower(),
                        "type": record.type,
                        "module": record.module,
                        "content": record.content,
                        "trace": trace
                    },
                    "values": [
                        [
                            str(int(time.time()) * 1000000000),
                            entry
                        ]
                    ]
                }
            ]
        }

        requests.post(
            url=self.grafanaUrl,
            auth=(self.grafanaUserId, self.grafanaToken),
            json=logs,
            headers={"Content-Type": "application/json"},
        )

    def _sendDiscord(self, record: logging.LogRecord):
        if record.exc_info:
            record.exc_info = None
        
        entry = self.format(record=record)
        
        embed = Embed(
            title="Extractor Alert",
            description=entry,
            url="https://kgusopio.grafana.net/explore",
            timestamp=datetime.now(),
            color=Colour.red()
        )
        embed.add_field(name="레벨", value=record.levelname.lower(), inline=False)
        embed.add_field(name="타입", value=record.type, inline=False)
        embed.add_field(name="모듈", value=record.module, inline=False)
        embed.set_footer(text="Extractor")

        webhook = SyncWebhook.from_url(url=self.discordUrl)
        webhook.send(embed=embed)