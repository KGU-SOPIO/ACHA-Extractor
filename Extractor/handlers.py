import logging
import traceback
from datetime import datetime

from discord import Colour, Embed, SyncWebhook


class ExtractorHandler(logging.Handler):
    def __init__(self, discordUrl: str):
        super().__init__()
        self.discordUrl = discordUrl
        self.streamHandler = logging.StreamHandler()

    def emit(self, record: logging.LogRecord):
        excInfo = record.exc_info
        record.exc_info = None

        entry = self.format(record=record)

        embed = Embed(
            title="Extractor Alert",
            description=entry,
            timestamp=datetime.now(),
            color=Colour.red(),
        )
        embed.add_field(name="레벨", value=record.levelname.lower(), inline=False)
        embed.add_field(name="타입", value=record.type, inline=False)
        embed.add_field(name="모듈", value=record.module, inline=False)
        embed.set_footer(text="Extractor")

        webhook = SyncWebhook.from_url(url=self.discordUrl)
        webhook.send(embed=embed)

        details = []
        if hasattr(record, "content") and record.content:
            details.append("Content: " + str(record.content))
        if hasattr(record, "data") and record.data:
            details.append("Data: " + str(record.data))

        excText = "".join(traceback.format_exception(*excInfo))
        details.append(excText)

        record.msg = f"{record.getMessage()}\n" + "\n".join(details)

        self.streamHandler.emit(record=record)


class AnalystHandler(logging.Handler):
    def __init__(self, discordUrl: str):
        super().__init__()
        self.discordUrl = discordUrl

    def emit(self, record: logging.LogRecord):
        entry = self.format(record=record)
        embed = Embed(
            title="Extractor Info",
            description=entry,
            timestamp=datetime.now(),
            color=Colour.blue(),
        )
        embed.set_footer(text="Extractor")

        webhook = SyncWebhook.from_url(url=self.discordUrl)
        webhook.send(embed=embed)
