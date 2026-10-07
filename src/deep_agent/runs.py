"""Single-worker queue; request cancellation never implies remote cancellation."""

import asyncio
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Lease:
    id: str
    viewer: str
    session: str
    ready: asyncio.Event
    acquired: bool = False


class RunCoordinator:
    def __init__(self):
        self.leases: list[Lease] = []

    def reserve(self, viewer: str, session: str) -> Lease | None:
        if any(lease.viewer == viewer for lease in self.leases) or len(self.leases) >= 6:
            return None
        lease = Lease(str(uuid4()), viewer, session, asyncio.Event())
        self.leases.append(lease)
        if len(self.leases) == 1:
            lease.ready.set()
        return lease

    async def acquire(self, lease: Lease) -> None:
        await lease.ready.wait()
        lease.acquired = True

    def release(self, lease: Lease) -> None:
        if lease in self.leases:
            self.leases.remove(lease)
            if self.leases:
                self.leases[0].ready.set()

    def busy_session(self, session: str) -> bool:
        return any(lease.session == session for lease in self.leases)
