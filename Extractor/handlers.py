import logging
from datetime import datetime

from discord import Colour, Embed, SyncWebhook


class ExtractorHandler(logging.Handler):
    def __init__(self, discordUrl: str):
        super().__init__()
        self.discordUrl = discordUrl

    def emit(self, record: logging.LogRecord):
        if record.exc_info:
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
