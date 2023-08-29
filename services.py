import asyncio
import curses

EXPLOSION_FRAMES = [
    """\
           (_)
       (  (   (  (
      () (  (  )
        ( )  ()
    """,
    """\
           (_)
       (  (   (
         (  (  )
          )  (
    """,
    """\
            (
          (   (
         (     (
          )  (
    """,
    """\
            (
              (
            (
    """,
]


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 16
    elif year < 1998:
        return 14
    elif year < 2011:
        return 10
    elif year < 2020:
        return 8
    elif year < 2040:
        return 6
    else:
        return 4


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


async def explode(canvas, center_row, center_column):
    rows, columns = get_frame_size(EXPLOSION_FRAMES[0])
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in EXPLOSION_FRAMES:
        draw_frame(canvas, corner_row, corner_column, frame)

        await asyncio.sleep(0)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
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


def load_frames(frames_of, num_photos):
    frames = []
    for frame_num in range(1, num_photos + 1):
        with open(f"animations/{frames_of}_frame_{frame_num}.txt", "r") as file:
            frames.append(file.read())

    return frames
