from ..common import (
    _ULCABaseInferenceRequest,
    _ULCAText,
    _ULCATxtLangDetectionInferenceConfig,
)


class ULCATxtLangDetectionInferenceRequest(_ULCABaseInferenceRequest):
    input: list[_ULCAText]
    config: _ULCATxtLangDetectionInferenceConfig
