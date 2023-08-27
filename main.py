import asyncio
import curses
import random
import time

from itertools import cycle

from obstacles import Obstacle
from physics import update_speed
from services import draw_frame, get_frame_size, explode

TIC_TIMEOUT = 0.1
STARS_AMOUNT = 100

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

FRAME_ROW_START = 1
FRAME_COLUMN_START = 1
FRAME_ROW_LIMIT = 2
FRAME_COLUMN_LIMIT = 2

ROW_SPEED = 0
COLUMN_SPEED = 0


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


async def fly_garbage(canvas, column, coroutines, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    frame_height, frame_width = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, frame_height, frame_width)
    obstacles.append(obstacle)

    while row < rows_number:
        if obstacle in obstacles_in_last_collisions:
            draw_frame(canvas, *obstacle.get_bounding_box_corner_pos(), obstacle.get_bounding_box_frame(),
                       negative=True)

            center_row = obstacle.row + obstacle.rows_size // 2
            center_column = obstacle.column + obstacle.columns_size // 2
            coroutines.append(explode(canvas, center_row, center_column))
            obstacles_in_last_collisions.remove(obstacle)
            obstacles.remove(obstacle)
            return

        draw_frame(canvas, *obstacle.get_bounding_box_corner_pos(), obstacle.get_bounding_box_frame(), negative=True)
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)

        row += speed
        obstacle.row = row
        obstacle.column = column

        draw_frame(canvas, *obstacle.get_bounding_box_corner_pos(), obstacle.get_bounding_box_frame())


async def fill_orbit_with_garbage(canvas, garbage_frames, coroutines):
    while True:
        garbage_frame = random.choice(garbage_frames)
        rows, columns = canvas.getmaxyx()
        frame_height, frame_width = get_frame_size(garbage_frame)
        column = random.randint(1, columns - frame_width - 1)

        coroutines.append(fly_garbage(canvas, column, coroutines, garbage_frame))
        await sleep(random.randint(0, 40))


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def show_gameover(canvas):
    with open("animations/game_over.txt", "r") as file:
        game_over_frame = file.read()

    rows, columns = canvas.getmaxyx()
    frame_height, frame_width = get_frame_size(game_over_frame)

    row = (rows - frame_height) // 2
    column = (columns - frame_width) // 2

    while True:
        draw_frame(canvas, row, column, game_over_frame)
        await asyncio.sleep(0)


async def run_spaceship(canvas, frames_cycle, coroutines):
    global ROW_SPEED, COLUMN_SPEED
    rows, columns = canvas.getmaxyx()
    row = rows // 2
    column = columns // 2
    frame = next(frames_cycle)

    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        ROW_SPEED, COLUMN_SPEED = update_speed(
            ROW_SPEED, COLUMN_SPEED,
            rows_direction, columns_direction
        )

        frame_height, frame_width = get_frame_size(frame)
        draw_frame(canvas, row, column, frame, negative=True)

        row += ROW_SPEED
        column += COLUMN_SPEED
        row = min(max(row, 1), rows - frame_height - 1)
        column = min(max(column, 1), columns - frame_width - 1)

        for obstacle in obstacles:
            if obstacle.has_collision(row, column, frame_height, frame_width):
                center_row = row + frame_height // 2
                center_column = column + frame_width // 2
                coroutines.append(explode(canvas, center_row, center_column))
                draw_frame(canvas, row, column, frame, negative=True)
                coroutines.append(show_gameover(canvas))
                return

        if space_pressed:
            fire_coroutine = fire(canvas, row, column + frame_width // 2, coroutines)
            coroutines.append(fire_coroutine)

        frame = next(frames_cycle)
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    await sleep(offset_tics)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(canvas, start_row, start_column, coroutines, rows_speed=-0.3, columns_speed=0):
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
        for obstacle in obstacles:
            if obstacle.has_collision(round(row), round(column)):
                center_row = obstacle.row + obstacle.rows_size // 2
                center_column = obstacle.column + obstacle.columns_size // 2
                coroutines.append(explode(canvas, center_row, center_column))
                obstacles_in_last_collisions.append(obstacle)
                return

        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def load_frames(frames_of, num_photos):
    frames = []
    for frame_num in range(1, num_photos + 1):
        with open(f"animations/{frames_of}_frame_{frame_num}.txt", "r") as file:
            frames.append(file.read())

    return frames


def draw(canvas):
    global obstacles, obstacles_in_last_collisions
    obstacles = []
    obstacles_in_last_collisions = []
    canvas.border()
    curses.curs_set(False)
    canvas.nodelay(True)
    rows, columns = canvas.getmaxyx()

    coroutines = [
        blink(
            canvas,
            random.randint(FRAME_ROW_START, rows - FRAME_ROW_LIMIT),
            random.randint(FRAME_COLUMN_START, columns - FRAME_COLUMN_LIMIT),
            symbol=random.choice('+*.:'),
            offset_tics=random.randint(0, 10)
        ) for _ in range(STARS_AMOUNT)
    ]

    garbage_frames = load_frames('garbage', 5)
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_frames, coroutines))

    spaceship_frames = load_frames('spaceship', 2)
    spaceship_doubled_frames = [frame for frame in spaceship_frames for _ in range(2)]
    spaceship_cycle = cycle(spaceship_doubled_frames)
    spaceship = run_spaceship(canvas, spaceship_cycle, coroutines)
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
