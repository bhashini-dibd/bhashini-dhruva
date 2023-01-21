import traceback
from fastapi import Depends

from exception.base_error import BaseError
from ..error.errors import Errors
from ..domain.request import ServiceViewRequest
from ..domain.response import ServiceViewResponse
from ..repository import ModelRepository, ServiceRepository


class DetailsService:
    def __init__(
        self,
        service_repository: ServiceRepository = Depends(ServiceRepository),
        model_repository: ModelRepository = Depends(ModelRepository),
    ) -> None:
        self.service_repository = service_repository
        self.model_repository = model_repository

    def get_service_details(self, request: ServiceViewRequest) -> ServiceViewResponse:
        try:
            service = self.service_repository.find_by_id(request.serviceId)
        except Exception:
            raise BaseError(Errors.DHRUVA104.value, traceback.format_exc())

        try:
            model = self.model_repository.find_by_id(service.modelId)
        except Exception:
            raise BaseError(Errors.DHRUVA105.value, traceback.format_exc())

        return ServiceViewResponse(**service.dict(), model=model)
