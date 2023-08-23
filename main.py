import asyncio
import curses
import random
import time

TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol='*'):
    for _ in range(random.randint(0, 10)):
        await asyncio.sleep(0)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def draw(canvas):
    canvas.border()
    curses.curs_set(False)
    stars_amount = 100
    max_y, max_x = canvas.getmaxyx()
    
    coroutines = [
        blink(
            canvas,
            random.randint(1, max_y - 1),
            random.randint(1, max_x - 1),
            symbol=random.choice('+*.:')
        ) for _ in range(stars_amount)
    ]

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
