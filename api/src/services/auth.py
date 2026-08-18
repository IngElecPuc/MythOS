from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.config.config import Settings
from src.core.exceptions import InvalidCredentialsError
from src.core.security import (
    BcryptPasswordHasher,
    HmacSecretHasher,
    JwtAccessTokenService,
    OpaqueTokenGenerator,
    PrincipalType,
)
from src.models.base import as_utc
from src.models.credentials import RefreshToken
from src.repositories.authorization import AuthorizationRepository
from src.repositories.credentials import (
    ApiKeyRepository,
    RefreshTokenRepository,
    ServiceClientRepository,
)
from src.repositories.user import UserRepository
from src.schemas.auth import (
    AccessTokenResponse,
    AuthenticatedPrincipal,
    ServicePrincipal,
    TokenPairResponse,
    UserPrincipal,
)


class AuthenticationService:
    def __init__(
        self,
        *,
        settings: Settings,
        users: UserRepository,
        authorization: AuthorizationRepository,
        refresh_tokens: RefreshTokenRepository,
        service_clients: ServiceClientRepository,
        api_keys: ApiKeyRepository,
        password_hasher: BcryptPasswordHasher,
        access_tokens: JwtAccessTokenService,
        refresh_token_hasher: HmacSecretHasher,
        api_key_hasher: HmacSecretHasher,
    ) -> None:
        self._settings = settings
        self._users = users
        self._authorization = authorization
        self._refresh_tokens = refresh_tokens
        self._service_clients = service_clients
        self._api_keys = api_keys
        self._password_hasher = password_hasher
        self._access_tokens = access_tokens
        self._refresh_token_hasher = refresh_token_hasher
        self._api_key_hasher = api_key_hasher

    def login(self, username: str, password: str) -> TokenPairResponse:
        user = self._users.get_by_username(username.strip().lower())
        if (
            user is None
            or not user.is_active
            or not self._password_hasher.verify(password, user.password_hash)
        ):
            raise InvalidCredentialsError()

        permissions = self._authorization.user_permissions(user.id)
        return self._issue_user_token_pair(
            user_id=user.id,
            token_version=user.token_version,
            permissions=permissions,
        )

    def refresh(self, raw_refresh_token: str) -> TokenPairResponse:
        now = datetime.now(UTC)
        token_hash = self._refresh_token_hasher.hash(raw_refresh_token)
        stored_token = self._refresh_tokens.get_for_update(token_hash)
        if stored_token is None:
            raise InvalidCredentialsError()

        if stored_token.revoked_at is not None:
            self._refresh_tokens.revoke_family(stored_token.family_id, now)
            raise InvalidCredentialsError(commit_transaction=True)

        if as_utc(stored_token.expires_at) <= now:
            raise InvalidCredentialsError()

        user = self._users.get(stored_token.user_id)
        if (
            user is None
            or not user.is_active
            or stored_token.token_version != user.token_version
        ):
            raise InvalidCredentialsError()

        stored_token.revoked_at = now
        permissions = self._authorization.user_permissions(user.id)
        pair = self._issue_user_token_pair(
            user_id=user.id,
            token_version=user.token_version,
            permissions=permissions,
            family_id=stored_token.family_id,
        )

        replacement_hash = self._refresh_token_hasher.hash(pair.refresh_token)
        replacement = self._refresh_tokens.get_for_update(replacement_hash)
        stored_token.replaced_by_token_id = replacement.id if replacement else None
        return pair

    def logout(self, raw_refresh_token: str) -> None:
        token_hash = self._refresh_token_hasher.hash(raw_refresh_token)
        stored_token = self._refresh_tokens.get_for_update(token_hash)
        if stored_token is not None and stored_token.revoked_at is None:
            stored_token.revoked_at = datetime.now(UTC)

    def client_credentials(
        self,
        *,
        client_id: str,
        client_secret: str,
        requested_scopes: set[str],
    ) -> AccessTokenResponse:
        client = self._service_clients.get_by_public_id(client_id)
        if (
            client is None
            or not client.is_active
            or not self._password_hasher.verify(
                client_secret,
                client.client_secret_hash,
            )
        ):
            raise InvalidCredentialsError()

        allowed = self._authorization.service_client_permissions(client.id)
        permissions = requested_scopes or allowed
        if not permissions.issubset(allowed):
            raise InvalidCredentialsError()

        access_token, expires_at = self._access_tokens.issue(
            subject=client.client_id,
            principal_type=PrincipalType.SERVICE,
            permissions=permissions,
        )
        return AccessTokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            scope=" ".join(sorted(permissions)),
        )

    def authenticate_access_token(self, token: str) -> AuthenticatedPrincipal:
        payload = self._access_tokens.decode(token)
        if payload.principal_type == PrincipalType.USER:
            try:
                user_id = int(payload.sub)
            except ValueError as exc:
                raise InvalidCredentialsError() from exc

            user = self._users.get(user_id)
            if (
                user is None
                or not user.is_active
                or payload.token_version != user.token_version
            ):
                raise InvalidCredentialsError()
            current_permissions = self._authorization.user_permissions(user.id)
            return UserPrincipal(
                id=user.id,
                username=user.username,
                email=user.email,
                permissions=set(payload.permissions) & current_permissions,
            )

        client = self._service_clients.get_by_public_id(payload.sub)
        if client is None or not client.is_active:
            raise InvalidCredentialsError()
        current_permissions = self._authorization.service_client_permissions(client.id)
        return ServicePrincipal(
            id=client.id,
            client_id=client.client_id,
            name=client.name,
            permissions=set(payload.permissions) & current_permissions,
        )

    def authenticate_api_key(self, raw_api_key: str) -> ServicePrincipal:
        key_hash = self._api_key_hasher.hash(raw_api_key)
        api_key = self._api_keys.get_by_hash(key_hash)
        now = datetime.now(UTC)
        if (
            api_key is None
            or api_key.revoked_at is not None
            or (api_key.expires_at is not None and as_utc(api_key.expires_at) <= now)
        ):
            raise InvalidCredentialsError()

        client = self._service_clients.get(api_key.service_client_id)
        if client is None or not client.is_active:
            raise InvalidCredentialsError()

        api_key.last_used_at = now
        self._api_keys.save(api_key)
        client_permissions = self._authorization.service_client_permissions(client.id)
        key_permissions = self._authorization.api_key_permissions(api_key.id)
        return ServicePrincipal(
            id=client.id,
            client_id=client.client_id,
            name=client.name,
            permissions=key_permissions & client_permissions,
        )

    def _issue_user_token_pair(
        self,
        *,
        user_id: int,
        token_version: int,
        permissions: set[str],
        family_id=None,
    ) -> TokenPairResponse:
        access_token, access_expires_at = self._access_tokens.issue(
            subject=str(user_id),
            principal_type=PrincipalType.USER,
            permissions=permissions,
            token_version=token_version,
        )
        raw_refresh_token = OpaqueTokenGenerator.generate("rt")
        now = datetime.now(UTC)
        refresh_record = RefreshToken(
            family_id=family_id or uuid4(),
            user_id=user_id,
            token_version=token_version,
            token_hash=self._refresh_token_hasher.hash(raw_refresh_token),
            expires_at=now + timedelta(days=self._settings.refresh_token_expire_days),
        )
        self._refresh_tokens.add(refresh_record)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_at=access_expires_at,
        )
