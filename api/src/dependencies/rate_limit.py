from __future__ import annotations

from fastapi import Request

from src.dependencies.services import RateLimiterDep, SettingsDep


class LoginRateLimit:
    def __call__(
        self,
        request: Request,
        limiter: RateLimiterDep,
        settings: SettingsDep,
    ) -> None:
        client_ip = request.client.host if request.client else "unknown"
        limiter.check(
            key=f"login:{client_ip}",
            limit=settings.login_rate_limit,
            window_seconds=settings.login_rate_window_seconds,
        )


class ClientTokenRateLimit:
    def __call__(
        self,
        request: Request,
        limiter: RateLimiterDep,
        settings: SettingsDep,
    ) -> None:
        client_ip = request.client.host if request.client else "unknown"
        limiter.check(
            key=f"client-token:{client_ip}",
            limit=settings.client_token_rate_limit,
            window_seconds=settings.client_token_rate_window_seconds,
        )
