import logging
from datetime import datetime

from discord import Colour, Embed, SyncWebhook


class ExtractorHandler(logging.Handler):
    def __init__(self, discordUrl: str):
        super().__init__()
        self.discordUrl = discordUrl
        self.streamHandler = logging.StreamHandler()

    def emit(self, record: logging.LogRecord):
        details = []
        if hasattr(record, "content") and record.content:
            details.append("Content: " + str(record.content))
        if hasattr(record, "data") and record.data:
            details.append("Data: " + str(record.data))

        streamRecord = record
        streamRecord.msg = f"{record.getMessage()}\n" + "\n".join(details)

        self.streamHandler.emit(record=streamRecord)

        # Traceback 제거
        record.exc_info = None
        record.exc_text = None

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
