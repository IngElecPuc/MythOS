from __future__ import annotations

from typing import Any, Protocol


class ExternalHttpClient(Protocol):
    """Contrato mínimo para clientes HTTP externos."""

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    async def post(
        self,
        path: str,
        *,
        json: dict[str, Any],
    ) -> dict[str, Any]: ...

    async def close(self) -> None: ...
