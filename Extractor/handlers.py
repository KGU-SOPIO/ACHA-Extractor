import logging
import os
import traceback
from datetime import datetime

from discord import Colour, Embed, SyncWebhook


class ExtractorHandler(logging.Handler):
    def __init__(self, discordUrl: str, logPath: str):
        super().__init__()
        self.discordUrl = discordUrl
        self.logPath = logPath

        os.makedirs(os.path.dirname(self.logPath), exist_ok=True)
        self.fileHandler = logging.FileHandler(self.logPath)

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
        if hasattr(record, "type") and record.type:
            embed.add_field(name="타입", value=record.type, inline=False)
        if hasattr(record, "module") and record.module:
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

        self.fileHandler.emit(record=record)


class PerformanceHandler(logging.Handler):
    def __init__(self, discordUrl: str):
        super().__init__()
        self.discordUrl = discordUrl

    def emit(self, record: logging.LogRecord):
        if hasattr(record, "time"):
            time = int(record.time)
            if time > 1500:
                embedColor = Colour.red()
            elif time > 1000:
                embedColor = Colour.orange()
            else:
                embedColor = Colour.blue()
        else:
            embedColor = Colour.blue()

        embed = Embed(
            title="Extractor Performance",
            timestamp=datetime.now(),
            color=embedColor,
        )
        if hasattr(record, "path"):
            embed.add_field(name="Path", value=record.path, inline=False)
        if hasattr(record, "method"):
            embed.add_field(name="Method", value=record.method, inline=True)
        if hasattr(record, "status"):
            embed.add_field(name="Status", value=record.status, inline=True)
        if hasattr(record, "time"):
            embed.add_field(name="Time", value=record.time, inline=True)
        embed.set_footer(text="Extractor")

        webhook = SyncWebhook.from_url(url=self.discordUrl)
        webhook.send(embed=embed)
