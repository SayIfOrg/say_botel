import functools
from contextlib import AsyncExitStack
from typing import Callable, AsyncGenerator, Any


def injector(*initializers: Callable[[], AsyncGenerator[Any, None]]):
    """
    Inject AsyncContextManagers to the in the provided order
    """

    def get_injects(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with AsyncExitStack() as stack:
                managers = [
                    await stack.enter_async_context(initializer())
                    for initializer in initializers
                ]
                return await func(*managers, *args, **kwargs)

        return wrapper

    return get_injects
