import asyncio
import itertools

# Globalny stan spinnera
spinner_running = False

async def spinner(label: str, stop_signal: asyncio.Event):
    global spinner_running
    if spinner_running:
        return
    spinner_running = True

    symbols = itertools.cycle(['-', '/', '|', '\\'])
    while not stop_signal.is_set():
        print(f'\r{next(symbols)} {label}', end='', flush=True)
        await asyncio.sleep(0.1)
    
    print('\r\x1b[2K', end='', flush=True)  # ANSI escape sequence to clear the current line
    spinner_running = False
