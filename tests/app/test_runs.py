import asyncio

import pytest

from deep_agent.runs import RunCoordinator


async def test_queue_is_bounded_and_cancelled_waiter_releases_capacity():
    coordinator = RunCoordinator()
    first = coordinator.reserve("a", "s1")
    assert first
    assert coordinator.reserve("a", "s2") is None
    await coordinator.acquire(first)
    waiting = [coordinator.reserve(str(i), "w" + str(i)) for i in range(5)]
    assert all(waiting)
    assert coordinator.reserve("extra", "extra") is None
    assert coordinator.busy_session("s1")
    task = asyncio.create_task(coordinator.acquire(waiting[0]))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    coordinator.release(waiting[0])
    assert coordinator.reserve("replacement", "new")
    coordinator.release(first)
    await coordinator.acquire(waiting[1])
    coordinator.release(waiting[1])
    assert not coordinator.busy_session("s1")
