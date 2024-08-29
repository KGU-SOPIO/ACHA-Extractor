import asyncio
import aiohttp

from Scrap.extractor.kutis import KutisExtractor
from Scrap.extractor.lms import LmsExtractor

class Extractor(KutisExtractor, LmsExtractor):
    def __init__(self, studentId, password):
        super().__init__(studentId, password)