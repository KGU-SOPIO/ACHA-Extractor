import time
import logging
import requests

class LokiHandler(logging.Handler):
    def __init__(self, grafanaUrl: str, grafanaUserId: str, grafanaToken: str):
        super().__init__()
        self.grafanaUrl = grafanaUrl
        self.grafanaUserId = grafanaUserId
        self.grafanaToken = grafanaToken
    
    def emit(self, record):
        entry = self.format(record)

        logs = {
            "streams": [
                {
                    "stream": {
                        "service": "extractor",
                        "level": record.levelname.lower(),
                        "type": record.type,
                        "content": record.content
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