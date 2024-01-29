import asyncio
import itertools

async def spinner(label: str, stop_signal: asyncio.Event):
    """Asynchronous spinner running in the background."""
    symbols = itertools.cycle(['-', '/', '|', '\\'])
    while not stop_signal.is_set():
        print(f'{next(symbols)} {label}')
        await asyncio.sleep(0.1)
    print('\r\x1b[2K', end='', flush=True)  # ANSI excape sequence to clear the current line
