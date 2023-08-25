import asyncio
import curses
import random
import time

from itertools import cycle

TIC_TIMEOUT = 0.1

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

FRAME_ROW_START = 1
FRAME_COLUMN_START = 1
FRAME_ROW_LIMIT = 2
FRAME_COLUMN_LIMIT = 2


def read_controls(canvas):
    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def animate_spaceship(canvas, frames_cycle):
    rows, columns = canvas.getmaxyx()
    row = rows // 2
    column = columns // 2
    frame = next(frames_cycle)

    while True:
        rows_direction, columns_direction, _ = read_controls(canvas)
        frame_height, frame_width = get_frame_size(frame)
        draw_frame(canvas, row, column, frame, negative=True)

        row = min(max(row + rows_direction, 1), rows - frame_height - 1)
        column = min(max(column + columns_direction, 1), columns - frame_width - 1)

        frame = next(frames_cycle)
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    for _ in range(offset_tics):
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


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def load_frames():
    frames = []
    for frame_num in range(1, 3):
        with open(f"animations/rocket_frame_{frame_num}.txt", "r") as file:
            frames.append(file.read())

    return frames


def draw(canvas):
    canvas.border()
    curses.curs_set(False)
    canvas.nodelay(True)
    stars_amount = 100
    rows, columns = canvas.getmaxyx()

    coroutines = [
        blink(
            canvas,
            random.randint(FRAME_ROW_START, rows - FRAME_ROW_LIMIT),
            random.randint(FRAME_COLUMN_START, columns - FRAME_COLUMN_LIMIT),
            symbol=random.choice('+*.:'),
            offset_tics=random.randint(0, 10)
        ) for _ in range(stars_amount)
    ]

    spaceship_frames = load_frames()
    spaceship_doubled_frames = [frame for frame in spaceship_frames for _ in range(2)]
    spaceship_cycle = cycle(spaceship_doubled_frames)
    spaceship = animate_spaceship(canvas, spaceship_cycle)
    coroutines.append(spaceship)

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
