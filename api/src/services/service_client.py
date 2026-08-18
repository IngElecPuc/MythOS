from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.core.exceptions import ResourceNotFoundError
from src.core.security import (
    BcryptPasswordHasher,
    HmacSecretHasher,
    OpaqueTokenGenerator,
)
from src.models.credentials import ApiKey, ServiceClient
from src.repositories.authorization import AuthorizationRepository
from src.repositories.credentials import ApiKeyRepository, ServiceClientRepository
from src.schemas.service_client import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
    ServiceClientCreate,
    ServiceClientCreated,
    ServiceClientRead,
)


class ServiceClientService:
    def __init__(
        self,
        *,
        clients: ServiceClientRepository,
        api_keys: ApiKeyRepository,
        authorization: AuthorizationRepository,
        password_hasher: BcryptPasswordHasher,
        api_key_hasher: HmacSecretHasher,
    ) -> None:
        self._clients = clients
        self._api_keys = api_keys
        self._authorization = authorization
        self._password_hasher = password_hasher
        self._api_key_hasher = api_key_hasher

    def create(self, data: ServiceClientCreate) -> ServiceClientCreated:
        raw_secret = OpaqueTokenGenerator.generate("cs")
        client = self._clients.add(
            ServiceClient(
                client_id=OpaqueTokenGenerator.generate("svc", bytes_count=12),
                name=data.name,
                description=data.description,
                client_secret_hash=self._password_hasher.hash(raw_secret),
            )
        )
        for code in data.permissions:
            permission = self._authorization.get_permission_by_code(code)
            if permission is None:
                raise ResourceNotFoundError("Permission", code)
            self._authorization.assign_permission_to_service_client(
                client.id,
                permission.id,
            )
        return ServiceClientCreated(
            **ServiceClientRead(
                id=client.id,
                client_id=client.client_id,
                name=client.name,
                description=client.description,
                is_active=client.is_active,
                permissions=set(data.permissions),
                created_at=client.created_at,
            ).model_dump(),
            client_secret=raw_secret,
        )

    def list(self) -> list[ServiceClientRead]:
        return [self._to_read(client) for client in self._clients.list()]

    def create_api_key(
        self,
        client_id: UUID,
        data: ApiKeyCreate,
    ) -> ApiKeyCreated:
        client = self._clients.get(client_id)
        if client is None:
            raise ResourceNotFoundError("ServiceClient", client_id)
        client_permissions = self._authorization.service_client_permissions(client.id)
        permissions = data.permissions or client_permissions
        missing = permissions - client_permissions
        if missing:
            raise ResourceNotFoundError("Permission", sorted(missing)[0])

        raw_key = OpaqueTokenGenerator.generate("ak")
        key_prefix = raw_key[:16]
        api_key = self._api_keys.add(
            ApiKey(
                service_client_id=client.id,
                name=data.name,
                key_prefix=key_prefix,
                key_hash=self._api_key_hasher.hash(raw_key),
                expires_at=data.expires_at,
            )
        )
        for code in permissions:
            permission = self._authorization.get_permission_by_code(code)
            if permission is None:
                raise ResourceNotFoundError("Permission", code)
            self._authorization.assign_permission_to_api_key(
                api_key.id,
                permission.id,
            )

        return ApiKeyCreated(
            id=api_key.id,
            name=api_key.name,
            api_key=raw_key,
            key_prefix=api_key.key_prefix,
            expires_at=api_key.expires_at,
            permissions=permissions,
            created_at=api_key.created_at,
        )

    def list_api_keys(self, client_id: UUID) -> list[ApiKeyRead]:
        if self._clients.get(client_id) is None:
            raise ResourceNotFoundError("ServiceClient", client_id)
        return [
            ApiKeyRead(
                id=key.id,
                name=key.name,
                key_prefix=key.key_prefix,
                expires_at=key.expires_at,
                revoked_at=key.revoked_at,
                last_used_at=key.last_used_at,
                permissions=self._authorization.api_key_permissions(key.id),
                created_at=key.created_at,
            )
            for key in self._api_keys.list_for_client(client_id)
        ]

    def revoke_api_key(self, key_id: UUID) -> None:
        api_key = self._api_keys.get(key_id)
        if api_key is None:
            raise ResourceNotFoundError("ApiKey", key_id)
        if api_key.revoked_at is None:
            api_key.revoked_at = datetime.now(UTC)
            self._api_keys.save(api_key)

    def _to_read(self, client: ServiceClient) -> ServiceClientRead:
        return ServiceClientRead(
            id=client.id,
            client_id=client.client_id,
            name=client.name,
            description=client.description,
            is_active=client.is_active,
            permissions=self._authorization.service_client_permissions(client.id),
            created_at=client.created_at,
        )
