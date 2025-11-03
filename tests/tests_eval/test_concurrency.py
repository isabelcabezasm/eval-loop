"""This test shows the difference between to use the global semaphore or the local one"""

import asyncio
from functools import wraps

import pytest

from eval.eval import CONCURRENCY_LIMIT, limit_concurrency


@pytest.mark.asyncio
async def test_semaphore_global_vs_local_decorator():
    """
    Test the difference between declaring semaphore outside vs inside the decorator.

    This test demonstrates two approaches:
    1. Global semaphore (shared across all decorated functions)
    2. Local semaphore (separate semaphore per decorated function)
    """

    # Test approach 1: Global semaphore pattern (similar to current implementation)
    # Create a fresh semaphore for this test to avoid event loop binding issues
    SHARED_SEMAPHORE = asyncio.Semaphore(3)

    global_concurrent_calls = 0
    max_global_concurrent = 0
    function_a_calls = 0
    function_b_calls = 0
    max_a_concurrent = 0
    max_b_concurrent = 0

    def limit_concurrency_shared(func):
        """Decorator using a shared semaphore (simulates current implementation)."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with SHARED_SEMAPHORE:
                return await func(*args, **kwargs)

        return wrapper

    @limit_concurrency_shared
    async def function_a_shared_semaphore(task_id: int) -> str:
        nonlocal global_concurrent_calls, max_global_concurrent
        nonlocal function_a_calls, max_a_concurrent
        global_concurrent_calls += 1
        function_a_calls += 1
        max_global_concurrent = max(max_global_concurrent, global_concurrent_calls)
        max_a_concurrent = max(max_a_concurrent, function_a_calls)

        await asyncio.sleep(0.1)  # Simulate work

        global_concurrent_calls -= 1
        function_a_calls -= 1
        return f"A-{task_id}"

    @limit_concurrency_shared
    async def function_b_shared_semaphore(task_id: int) -> str:
        nonlocal global_concurrent_calls, max_global_concurrent
        nonlocal function_b_calls, max_b_concurrent
        global_concurrent_calls += 1
        function_b_calls += 1
        max_global_concurrent = max(max_global_concurrent, global_concurrent_calls)
        max_b_concurrent = max(max_b_concurrent, function_b_calls)

        await asyncio.sleep(0.1)  # Simulate work

        global_concurrent_calls -= 1
        function_b_calls -= 1
        return f"B-{task_id}"

    # Test approach 2: Local semaphore pattern (alternative implementation)
    def limit_concurrency_per_function(limit: int = 3):
        """Decorator that creates a separate semaphore for each decorated function."""

        def decorator(func):
            semaphore = asyncio.Semaphore(limit)

            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with semaphore:
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    # Reset counters for the second test
    separate_a_calls = 0
    separate_b_calls = 0
    max_separate_a = 0
    max_separate_b = 0

    @limit_concurrency_per_function(limit=3)
    async def function_a_separate_semaphore(task_id: int) -> str:
        nonlocal separate_a_calls, max_separate_a
        separate_a_calls += 1
        max_separate_a = max(max_separate_a, separate_a_calls)

        await asyncio.sleep(0.1)  # Simulate work

        separate_a_calls -= 1
        return f"SA-{task_id}"

    @limit_concurrency_per_function(limit=3)
    async def function_b_separate_semaphore(task_id: int) -> str:
        nonlocal separate_b_calls, max_separate_b
        separate_b_calls += 1
        max_separate_b = max(max_separate_b, separate_b_calls)

        await asyncio.sleep(0.1)  # Simulate work

        separate_b_calls -= 1
        return f"SB-{task_id}"

    # Test 1: Shared semaphore (global semaphore pattern)
    # Create 4 tasks for each function (8 total tasks)
    tasks_shared = []
    tasks_shared.extend([function_a_shared_semaphore(i) for i in range(4)])
    tasks_shared.extend([function_b_shared_semaphore(i) for i in range(4)])

    results_shared = await asyncio.gather(*tasks_shared)

    # With shared semaphore (limit=3), total concurrent calls should not exceed 3
    assert max_global_concurrent == 3
    # Results should contain all expected values
    a_results = [r for r in results_shared if r.startswith("A-")]
    b_results = [r for r in results_shared if r.startswith("B-")]
    assert len(a_results) == 4
    assert len(b_results) == 4

    # Test 2: Separate semaphores per function
    tasks_separate = []
    tasks_separate.extend([function_a_separate_semaphore(i) for i in range(4)])
    tasks_separate.extend([function_b_separate_semaphore(i) for i in range(4)])

    results_separate = await asyncio.gather(*tasks_separate)

    # With separate semaphores, each function can run up to its limit concurrently
    # So we should see higher concurrency per function
    assert max_separate_a == 3  # Each function can use its full semaphore limit
    assert max_separate_b == 3
    # Total possible concurrent would be 3 + 3 = 6, much higher than shared limit of 3

    # Results should contain all expected values
    sa_results = [r for r in results_separate if r.startswith("SA-")]
    sb_results = [r for r in results_separate if r.startswith("SB-")]
    assert len(sa_results) == 4
    assert len(sb_results) == 4

    print("=== SHARED SEMAPHORE APPROACH ===")
    print(f"Max global concurrent: {max_global_concurrent}")
    print(f"Max function A concurrent: {max_a_concurrent}")
    print(f"Max function B concurrent: {max_b_concurrent}")
    semaphore_limit = SHARED_SEMAPHORE._value
    print(f"Total: Functions share the same semaphore (limit={semaphore_limit})")

    print("\n=== SEPARATE SEMAPHORES APPROACH ===")
    print(f"Max function A concurrent: {max_separate_a}")
    print(f"Max function B concurrent: {max_separate_b}")
    print(f"Total: Each function has its own semaphore (limit=3 each)")
    combined_concurrent = max_separate_a + max_separate_b
    print(f"Combined potential concurrent: {combined_concurrent}")
