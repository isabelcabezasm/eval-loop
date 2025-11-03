"""Tests for concurrency limiting functionality in eval module."""

import asyncio
from functools import wraps

import pytest

from eval.eval import CONCURRENCY_LIMIT, limit_concurrency


@pytest.mark.asyncio
async def test_concurrency_is_actually_limited():
    """Test that concurrency is actually limited to the semaphore value."""
    concurrent_calls = 0
    max_concurrent = 0

    @limit_concurrency
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
    assert max_concurrent == CONCURRENCY_LIMIT  # Should not exceed semaphore limit
    assert concurrent_calls == 0  # All tasks should be completed


@pytest.mark.asyncio
async def test_semaphore_releases_on_exception():
    """Test that semaphore is released when function raises exception."""

    @limit_concurrency
    async def failing_func() -> None:
        await asyncio.sleep(0.01)
        raise ValueError("Test exception")

    # Test that exception is propagated
    with pytest.raises(ValueError, match="Test exception"):
        await failing_func()

    # Test that semaphore is still usable after exception
    @limit_concurrency
    async def working_func() -> str:
        await asyncio.sleep(0.01)
        return "success"

    result = await working_func()
    assert result == "success"


@pytest.mark.asyncio
async def test_mixed_success_and_failure_scenarios():
    """Test successes and failures with concurrency limiting using limit_concurrency."""

    @limit_concurrency
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
