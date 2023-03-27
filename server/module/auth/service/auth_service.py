import math
import os
import secrets
import time
import traceback
from datetime import datetime
from typing import List

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from pydantic import EmailStr

from exception.base_error import BaseError
from exception.ulca_api_key_client_error import ULCAApiKeyClientError
from exception.ulca_api_key_server_error import ULCAApiKeyServerError
from module.auth.model import Session
from schema.auth.request import (
    CreateApiKeyRequest,
    GetAllApiKeysRequest,
    GetApiKeyQuery,
    RefreshRequest,
    SetApiKeyStatusQuery,
    SignInRequest,
    ULCAApiKeyRequest,
)
from schema.auth.request.set_api_key_status_query import ApiKeyAction
from schema.auth.response import SignInResponse, ULCAApiKeyDeleteResponse

from ..error import Errors
from ..model.api_key import ApiKey, ApiKeyCache
from ..repository import ApiKeyRepository, SessionRepository, UserRepository

load_dotenv()


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository = Depends(UserRepository),
        session_repository: SessionRepository = Depends(SessionRepository),
        api_key_repository: ApiKeyRepository = Depends(ApiKeyRepository),
    ) -> None:
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.api_key_repository = api_key_repository

    def validate_user(self, request: SignInRequest):
        try:
            user = self.user_repository.find_one({"email": request.email})
        except:
            raise BaseError(Errors.DHRUVA201.value, traceback.format_exc())

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Invalid credentials"},
            )

        ph = PasswordHasher()
        ph.check_needs_rehash(user.password)

        try:
            ph.verify(user.password, request.password)
        except VerifyMismatchError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Invalid credentials"},
            )
        except Exception:
            raise BaseError(Errors.DHRUVA202.value, traceback.format_exc())

        session = Session(
            user_id=ObjectId(str(user.id)),
            type="refresh",
            timestamp=datetime.now(),
        )

        try:
            id = self.session_repository.insert_one(session)
        except Exception:
            raise BaseError(Errors.DHRUVA203.value, traceback.format_exc())

        token = jwt.encode(
            {
                "sub": str(user.id),
                "name": user.name,
                "exp": (time.time() + 31536000),
                "iat": time.time(),
                "sess_id": str(id),
            },
            os.environ["JWT_SECRET_KEY"],
            algorithm="HS256",
            headers={"tok": "refresh"},
        )

        # create and return jwt
        return SignInResponse(email=user.email, token=token, role=user.role)

    def get_refresh_token(self, request: RefreshRequest):
        try:
            headers = jwt.get_unverified_header(request.token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid refresh token"},
            )

        if headers.get("tok") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid refresh token"},
            )

        try:
            claims = jwt.decode(
                request.token, key=os.environ["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid refresh token"},
            )

        session = Session(
            user_id=ObjectId(claims["sub"]),
            type="access",
            timestamp=datetime.now(),
        )

        try:
            id = self.session_repository.insert_one(session)
        except Exception:
            raise BaseError(Errors.DHRUVA203.value, traceback.format_exc())

        token = jwt.encode(
            {
                "sub": claims["sub"],
                "name": claims["name"],
                "exp": (time.time() + 2592000),
                "iat": time.time(),
                "sess_id": str(id),
            },
            os.environ["JWT_SECRET_KEY"],
            algorithm="HS256",
            headers={"tok": "access"},
        )

        return token

    def create_api_key(self, request: CreateApiKeyRequest, id: ObjectId):
        try:
            user_id = (
                id if not request.target_user_id else ObjectId(request.target_user_id)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid target user id"},
            )

        try:
            existing_api_key = self.api_key_repository.find_one(
                {"name": request.name, "user_id": user_id}
            )
        except Exception:
            raise BaseError(Errors.DHRUVA208.value, traceback.format_exc())

        if existing_api_key and request.regenerate:
            key = self.__regenerate_api_key(existing_api_key)
        elif existing_api_key and not request.regenerate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "API Key name already exists"},
            )
        else:
            key = self.__generate_new_api_key(request, user_id)

        return key

    def __mask_key(self, key: str):
        masked_key = key[:4] + (len(key) - 8) * "*" + key[-4:]
        return masked_key

    def __generate_new_api_key(self, request: CreateApiKeyRequest, id: ObjectId):
        key = secrets.token_urlsafe(48)
        api_key = ApiKey(
            name=request.name,
            api_key=key,
            masked_key=self.__mask_key(key),
            active=True,
            user_id=id,
            type=request.type.value,
            created_timestamp=datetime.now(),
        )

        try:
            inserted_id = self.api_key_repository.insert_one(api_key)
            api_key.id = inserted_id

            # Cache write
            api_key_cache = ApiKeyCache(**api_key.dict())
            api_key_cache.save()
        except Exception:
            raise BaseError(Errors.DHRUVA204.value, traceback.format_exc())

        return key

    def __regenerate_api_key(self, existing_api_key: ApiKey):
        key = secrets.token_urlsafe(48)
        existing_api_key.api_key = key
        existing_api_key.masked_key = self.__mask_key(key)

        try:
            self.api_key_repository.save(existing_api_key)

            # Cache write
            api_key_cache = ApiKeyCache(**existing_api_key.dict())
            api_key_cache.save()
        except Exception:
            raise BaseError(Errors.DHRUVA204.value, traceback.format_exc())

        return key

    def get_api_key(self, params: GetApiKeyQuery, id: ObjectId):
        try:
            user_id = (
                id if not params.target_user_id else ObjectId(params.target_user_id)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid target user id"},
            )

        try:
            key = self.api_key_repository.find_one(
                {"name": params.api_key_name, "user_id": user_id}
            )
        except Exception:
            raise BaseError(Errors.DHRUVA208.value, traceback.format_exc())

        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "API Key does not exist"},
            )

        return key

    def get_all_api_keys(self, params: GetAllApiKeysRequest, id: ObjectId):
        try:
            user_id = (
                id if not params.target_user_id else ObjectId(params.target_user_id)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid target user id"},
            )

        try:
            keys = self.api_key_repository.find({"user_id": user_id})
        except Exception:
            raise BaseError(Errors.DHRUVA204.value, traceback.format_exc())

        return keys

    def get_all_api_keys_with_usage(self, page, limit, target_user_id: str) -> List:
        """
        Fetches all API keys from the collection and calculates the total usage
        Args:
            - page: Current page
            - limit: Number of documents per page
            - target_user_id: User id to filter api keys with
        Returns:
            - List[APIKeys]
            - total_usage
            - total_pages
        """
        keys = self.api_key_repository.find({"user_id": ObjectId(target_user_id)})
        total_usage = sum(k.usage for k in keys)

        return (
            keys[(page - 1) * limit : page * limit],
            total_usage,
            math.ceil(len(keys) / limit),
        )

    def set_api_key_status(self, params: SetApiKeyStatusQuery, id: ObjectId):
        try:
            user_id = (
                id if not params.target_user_id else ObjectId(params.target_user_id)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid target user id"},
            )

        try:
            api_key = self.api_key_repository.find_one(
                {"name": params.api_key_name, "user_id": user_id}
            )
        except Exception:
            raise BaseError(Errors.DHRUVA208.value, traceback.format_exc())

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Api key not found"},
            )

        match params.action:
            case ApiKeyAction.ACTIVATE:
                api_key.activate()
            case ApiKeyAction.REVOKE:
                api_key.revoke()

        try:
            self.api_key_repository.save(api_key)

            # Cache write
            api_key_cache = ApiKeyCache(**api_key.dict())
            api_key_cache.save()
        except Exception:
            raise BaseError(Errors.DHRUVA209.value, traceback.format_exc())

        return api_key

    def set_api_key_status_ulca(self, request: ULCAApiKeyRequest, id: ObjectId):
        api_key_name = request.emailId + "/" + request.appName

        try:
            api_key = self.api_key_repository.find_one(
                {"name": api_key_name, "user_id": id}
            )
        except Exception:
            raise ULCAApiKeyServerError(Errors.DHRUVA208.value, traceback.format_exc())

        if not api_key:
            raise ULCAApiKeyClientError(status.HTTP_404_NOT_FOUND, "API Key not found")

        api_key.revoke()

        try:
            self.api_key_repository.save(api_key)

            # Cache write
            api_key_cache = ApiKeyCache(**api_key.dict())
            api_key_cache.save()
        except Exception:
            raise ULCAApiKeyServerError(Errors.DHRUVA208.value, traceback.format_exc())

        return ULCAApiKeyDeleteResponse(
            isRevoked=True, message="API Key successfully deleted"
        )