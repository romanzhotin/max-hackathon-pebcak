import logging
from typing import Any

import httpx

from config import API_BASE_URL, API_TIMEOUT

log = logging.getLogger(__name__)


class ApiError(Exception):
    pass


class BackendClient:
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = API_TIMEOUT):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_user(self, max_id: int) -> dict | None:
        try:
            r = await self._client.get(f"/users/{max_id}")
        except httpx.RequestError as e:
            log.exception("get_user: network error")
            raise ApiError("Сервис временно недоступен, попробуй позже.") from e
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            raise ApiError(f"Backend вернул {r.status_code}")
        return r.json()

    async def upsert_user(self, max_id: int, city: str, categories: list[str]) -> None:
        try:
            r = await self._client.post(
                f"/users/{max_id}",
                json={"city": city, "categories": categories},
            )
        except httpx.RequestError as e:
            log.exception("upsert_user: network error")
            raise ApiError("Не удалось сохранить профиль, попробуй позже.") from e
        if r.status_code >= 400:
            raise ApiError(f"Backend вернул {r.status_code}")

    async def get_events(
        self,
        city: str,
        event_type: str,
        min_price: int | None = None,
        max_price: int | None = None,
        max_date: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if min_price is not None:
            params["minPrice"] = min_price
        if max_price is not None:
            params["maxPrice"] = max_price
        if max_date is not None:
            params["maxDate"] = max_date

        try:
            r = await self._client.get(f"/Events/{city}/{event_type}", params=params)
        except httpx.RequestError as e:
            log.exception("get_events: network error")
            raise ApiError("Не могу получить события, попробуй позже.") from e
        if r.status_code >= 400:
            raise ApiError(f"Backend вернул {r.status_code}")
        return r.json()


backend = BackendClient()