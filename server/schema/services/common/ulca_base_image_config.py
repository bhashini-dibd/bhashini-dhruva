from typing import Optional ,List

from pydantic import BaseModel

from .image_format import ImageFormat
from .ulca_language import _ULCALanguage


class _ULCABaseImageConfig(BaseModel):
    languages: List[_ULCALanguage]
