import functools
from contextlib import AsyncExitStack
from typing import Callable, AsyncGenerator, Any


def injector(*initializers: tuple[Callable[[Any], AsyncGenerator[Any, None]], tuple]):
    """
    Inject AsyncContextManagers to the func in the provided order
    """

    def get_injects(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with AsyncExitStack() as stack:
                managers = [
                    await stack.enter_async_context(initializer[0](*initializer[1]))
                    for initializer in initializers
                ]
                return await func(*managers, *args, **kwargs)

        return wrapper

    return get_injects


def method_injector(*initializers: str):
    """
    Inject AsyncContextManagers to the method in the provided order
    """

    def get_injects(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            async with AsyncExitStack() as stack:
                managers = []
                for i in initializers:
                    initializer: tuple[
                        Callable[[Any], AsyncGenerator[Any, None]], tuple
                    ] = getattr(self, i)
                    managers.append(
                        await stack.enter_async_context(initializer[0](*initializer[1]))
                    )

                return await func(self, *managers, *args, **kwargs)

        return wrapper

    return get_injects
