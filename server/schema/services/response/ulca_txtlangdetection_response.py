from typing import List, Optional

from pydantic import BaseModel

from ..common import (
    _ULCATaskType,
    _ULCALangPairMultisuggestion,
    _ULCATxtLangDetectionInferenceConfig,
)


class ULCATxtLangDetectionInferenceResponse(BaseModel):
    taskType: _ULCATaskType = _ULCATaskType.TXTLANGDETECTION
    output: List[_ULCALangPairMultisuggestion]
    config: Optional[_ULCATxtLangDetectionInferenceConfig] = None
