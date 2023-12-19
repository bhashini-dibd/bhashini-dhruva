from typing import Optional ,List

from pydantic import BaseModel

from .image_format import ImageFormat
from .ulca_language import _ULCALanguage


class _ULCABaseImageConfig(BaseModel):
    isMultilingual:Optional[bool] =  False
    languages: Optional[List[_ULCALanguage]]
    language : Optional[_ULCALanguage]
