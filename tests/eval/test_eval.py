"""Tests for concurrency limiting functionality in eval module."""

import asyncio
from asyncio import Condition, create_task
from functools import wraps

import pytest

from eval.eval import limit_concurrency


@pytest.mark.asyncio
async def test_concurrency_is_actually_limited():
    """Test that concurrency is actually limited to the semaphore value."""
    concurrent_calls = 0
    max_concurrent = 0

    @limit_concurrency(2)
    async def monitored_func(task_id: int) -> int:
        nonlocal concurrent_calls, max_concurrent
        concurrent_calls += 1
        max_concurrent = max(max_concurrent, concurrent_calls)
        # Simulate some work
        await asyncio.sleep(0.1)
        concurrent_calls -= 1
        return task_id

    # Create 10 tasks (more than concurrency limit of CONCURRENCY_LIMIT)
    tasks = [monitored_func(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    # Check results
    assert results == list(range(10))
    assert max_concurrent == 2  # Should not exceed semaphore limit
    assert concurrent_calls == 0  # All tasks should be completed


@pytest.mark.asyncio
async def test_semaphore_releases_on_exception():
    """Test that semaphore is released when function raises exception."""

    @limit_concurrency()
    async def failing_func() -> None:
        await asyncio.sleep(0.01)
        raise ValueError("Test exception")

    # Test that exception is propagated
    with pytest.raises(ValueError, match="Test exception"):
        await failing_func()

    # Test that semaphore is still usable after exception
    @limit_concurrency()
    async def working_func() -> str:
        await asyncio.sleep(0.1)
        return "success"

    result = await working_func()
    assert result == "success"


@pytest.mark.asyncio
async def test_mixed_success_and_failure_scenarios():
    """Test successes and failures with concurrency limiting using limit_concurrency."""

    @limit_concurrency()
    async def mixed_func(task_id: int) -> int:
        await asyncio.sleep(0.01)
        if task_id % 3 == 0:
            raise ValueError(f"Task {task_id} failed")
        return task_id * 2

    tasks = [mixed_func(i) for i in range(6)]
    # Use gather with return_exceptions=True to capture both results and exceptions
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Check that we got expected results and exceptions
    expected = [
        ValueError,  # task 0: 0 % 3 == 0
        2,  # task 1: 1 * 2 = 2
        4,  # task 2: 2 * 2 = 4
        ValueError,  # task 3: 3 % 3 == 0
        8,  # task 4: 4 * 2 = 8
        10,  # task 5: 5 * 2 = 10
    ]
    for i, (result, expected_type) in enumerate(zip(results, expected)):
        if expected_type is ValueError:
            assert isinstance(result, ValueError)
            assert f"Task {i} failed" in str(result)
        else:
            assert result == expected_type


# custom synchronization primitive
# thread-safe set with notification capabilities
# this will help us to test concurrency behavior
class SignalBox:
    def __init__(self):
        self._set = set()

        # coordination between coroutines
        # when one coroutine adds an item, it can wake up others that are waiting.
        self._condition = Condition()

    #  Adds an item to the set and notifies all waiting coroutines
    async def record(self, item: int) -> None:
        async with self._condition:
            self._set.add(item)
            self._condition.notify_all()

    def __len__(self) -> int:
        return len(self._set)

    def __iter__(self):
        return iter(self._set)

    # Waits until the set contains at least count items
    async def wait_until_total(self, count: int, /) -> None:
        async with self._condition:
            while len(self._set) < count:
                await self._condition.wait()

    # Waits until a specific item appears in the set
    async def wait_for_item(self, item: int, /) -> None:
        async with self._condition:
            while item not in self._set:
                await self._condition.wait()


@pytest.mark.asyncio
async def test_concurrency_limit_with_controlled_advancement():
    # arrange
    started = SignalBox()
    finished = SignalBox()

    @limit_concurrency(2)
    async def execute(id: int) -> None:
        await started.record(id)
        await finished.wait_for_item(id)

    # act + assert
    for i in range(1, 4):
        # create 3 tasks (1, 2, 3)
        _ = create_task(execute(i))

    # check that exactly two have started
    await started.wait_until_total(2)  # Waits until exactly 2 tasks have started,
    assert len(started) == 2  # confirms the third is blocked

    # finish one of the started tasks
    await finished.record(
        next(iter(started))
    )  # finish one of the started tasks, this unblock the third one

    # assert that now all tasks can start
    await started.wait_until_total(3)
    assert len(started) == 3

    # finish all tasks
    for item in started:
        await finished.record(item)
