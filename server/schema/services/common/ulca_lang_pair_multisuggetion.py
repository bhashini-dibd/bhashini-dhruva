from typing import List , Optional

from .ulca_text import _ULCAText
from pydantic import BaseModel

class _ULCALangPrediction(BaseModel):
    langCode : str
    scriptCode :Optional[str]
    langScore :Optional[float]

class _ULCALangPairMultisuggestion(_ULCAText):
    source : str
    langPrediction: List[_ULCALangPrediction]
