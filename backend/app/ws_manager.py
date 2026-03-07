"""Gerenciador de conexões WebSocket — singleton compartilhado pela app."""

from __future__ import annotations

import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.active[session_id] = websocket

    def disconnect(self, session_id: str) -> None:
        self.active.pop(session_id, None)

    async def send(self, session_id: str, data: dict) -> None:
        ws = self.active.get(session_id)
        if ws:
            await ws.send_text(json.dumps(data))

    async def broadcast(self, data: dict) -> None:
        for ws in self.active.values():
            await ws.send_text(json.dumps(data))


manager = ConnectionManager()
