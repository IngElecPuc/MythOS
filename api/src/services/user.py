from __future__ import annotations

from src.config.config import Settings
from src.core.exceptions import ResourceConflictError, ResourceNotFoundError
from src.core.pagination import Page, PaginationParams
from src.core.security import PasswordHasher
from src.models.user import User, utc_now
from src.repositories.authorization import AuthorizationRepository
from src.repositories.user import UserRepository
from src.schemas.user import UserCreate, UserRead, UserReplace, UserUpdate
from src.schemas.user_query import UserFilterParams


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        authorization: AuthorizationRepository,
        password_hasher: PasswordHasher,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._authorization = authorization
        self._password_hasher = password_hasher
        self._settings = settings

    def list_users(
        self,
        *,
        pagination: PaginationParams,
        filters: UserFilterParams,
    ) -> Page[UserRead]:
        users, total = self._repository.list(
            offset=pagination.offset,
            limit=pagination.page_size,
            filters=filters,
        )
        return Page[UserRead].build(
            items=[UserRead.model_validate(user) for user in users],
            total=total,
            params=pagination,
        )

    def get_user(self, user_id: int) -> UserRead:
        return UserRead.model_validate(self._get_user_model(user_id))

    def create_user(self, data: UserCreate) -> UserRead:
        self._ensure_unique(username=data.username, email=str(data.email))
        user = self._repository.add(
            User(
                username=data.username,
                email=str(data.email),
                password_hash=self._password_hasher.hash(data.password),
            )
        )
        role = self._authorization.get_role_by_name(self._settings.default_user_role)
        if role is None:
            raise RuntimeError(
                f"No existe el rol por defecto '{self._settings.default_user_role}'. "
                "Ejecuta el seed inicial."
            )
        self._authorization.assign_role_to_user(user.id, role.id)
        return UserRead.model_validate(user)

    def replace_user(self, user_id: int, data: UserReplace) -> UserRead:
        user = self._get_user_model(user_id)
        self._ensure_unique(
            username=data.username,
            email=str(data.email),
            current_user_id=user_id,
        )
        user.username = data.username
        user.email = str(data.email)
        user.password_hash = self._password_hasher.hash(data.password)
        user.token_version += 1
        user.updated_at = utc_now()
        return UserRead.model_validate(self._repository.save(user))

    def update_user(self, user_id: int, data: UserUpdate) -> UserRead:
        user = self._get_user_model(user_id)
        update_data = data.model_dump(exclude_unset=True)
        self._ensure_unique(
            username=update_data.get("username", user.username),
            email=str(update_data.get("email", user.email)),
            current_user_id=user_id,
        )
        password = update_data.pop("password", None)
        if password is not None:
            user.password_hash = self._password_hasher.hash(password)
            user.token_version += 1
        if "email" in update_data:
            update_data["email"] = str(update_data["email"])
        for field, value in update_data.items():
            setattr(user, field, value)
        user.updated_at = utc_now()
        return UserRead.model_validate(self._repository.save(user))

    def delete_user(self, user_id: int) -> None:
        self._repository.delete(self._get_user_model(user_id))

    def _get_user_model(self, user_id: int) -> User:
        user = self._repository.get(user_id)
        if user is None:
            raise ResourceNotFoundError("User", user_id)
        return user

    def _ensure_unique(
        self,
        *,
        username: str,
        email: str,
        current_user_id: int | None = None,
    ) -> None:
        user = self._repository.get_by_username(username)
        if user is not None and user.id != current_user_id:
            raise ResourceConflictError(
                "El nombre de usuario ya está registrado.",
                details={"field": "username"},
            )
        user = self._repository.get_by_email(email)
        if user is not None and user.id != current_user_id:
            raise ResourceConflictError(
                "El correo electrónico ya está registrado.",
                details={"field": "email"},
            )
