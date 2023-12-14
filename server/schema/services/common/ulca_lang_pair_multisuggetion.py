from typing import List , Optional

from .ulca_text import _ULCAText
from pydantic import BaseModel

class _ULCALangPrediction(BaseModel):
    langCode : str
    ScriptCode :Optional[str]
    langScore :Optional[float]

class _ULCALangPairMultisuggestion(_ULCAText):
    langPrediction: List[_ULCALangPrediction]
