"""EventBus: publish/subscribe between modules."""

import asyncio

from src.core.events import EventBus, R2Events, create_event


def run(coro):
    return asyncio.run(coro)


def test_subscriber_receives_event():
    async def scenario():
        bus = EventBus()
        received = []
        await bus.subscribe(R2Events.DEVICE_DISCOVERED, lambda e: received.append(e.data["ip"]))
        await bus.publish(create_event(R2Events.DEVICE_DISCOVERED, {"ip": "192.0.2.1"}, "test"))
        return received, bus.get_stats()

    received, stats = run(scenario())
    assert received == ["192.0.2.1"]
    assert stats["events_published"] == 1
    assert stats["events_processed"] == 1


def test_async_handler_and_other_events_ignored():
    async def scenario():
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event.name)

        await bus.subscribe(R2Events.NETWORK_SCAN_COMPLETED, handler)
        await bus.publish(create_event(R2Events.NETWORK_SCAN_STARTED, {}, "test"))
        await bus.publish(create_event(R2Events.NETWORK_SCAN_COMPLETED, {}, "test"))
        return received

    assert run(scenario()) == [R2Events.NETWORK_SCAN_COMPLETED]


def test_failing_handler_is_counted_not_raised():
    async def scenario():
        bus = EventBus()

        def broken(event):
            raise RuntimeError("boom")

        await bus.subscribe(R2Events.SYSTEM_ERROR, broken)
        await bus.publish(create_event(R2Events.SYSTEM_ERROR, {}, "test"))
        return bus.get_stats()

    assert run(scenario())["handler_errors"] == 1


def test_no_events_after_shutdown():
    async def scenario():
        bus = EventBus()
        received = []
        await bus.subscribe(R2Events.SYSTEM_SHUTDOWN, lambda e: received.append(e))
        await bus.shutdown()
        await bus.publish(create_event(R2Events.SYSTEM_SHUTDOWN, {}, "test"))
        return received, bus.is_shutdown_requested()

    received, stopped = run(scenario())
    assert received == []
    assert stopped is True
