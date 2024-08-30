import asyncio
import aiohttp

from Scrap.extractor.parts.kutis import KutisExtractor
from Scrap.extractor.parts.lms import LmsExtractor

class Extractor(KutisExtractor, LmsExtractor):
    def __init__(self, studentId, password):
        KutisExtractor.__init__(self, studentId, password)
        LmsExtractor.__init__(self, studentId, password)

    async def kutis(self):
        return await self.getTimetable()

    async def lms(self):
        return await self._getCourseList()