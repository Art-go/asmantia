import random

from PIL import Image, ImageDraw
from Engine import Vec2

atlas_size = Vec2(512, 512)
img = Image.new("RGB", atlas_size.tuple)
draw = ImageDraw.ImageDraw(img)

available = [(Vec2(), atlas_size.copy())]
n = 16


def add(size):
    global n
    for i, [pos, maxsize] in enumerate(available):
        if maxsize.lt_or(size):  # maxsize.x < size.x or maxsize.y < size.y
            continue
        print(pos, maxsize)
        available.pop(i)
        draw.rectangle((*pos, *(pos + size)), (n, 60, n))
        n += 16
        if n > 256:
            n = 16
        tr = (pos + size.vx, maxsize - size.vx)  # TR
        bl = (pos + size.vy, maxsize - size.vy)  # BL
        rect_pos = pos
        break
    else:
        print("No place found")
        raise RuntimeError
    # update maxsize
    for pos, maxsize in available:
        if pos.ge_or(rect_pos + size) or rect_pos.ge_or(pos + maxsize):
            continue
        if pos.y < rect_pos.y:
            maxsize.y = rect_pos.y - pos.y
        if pos.x < rect_pos.x:
            maxsize.x = rect_pos.x - pos.x

    available.extend((tr, bl))
    available.sort(key=lambda key: key[0].x * 512 + key[0].y)

    print(size, rect_pos)
    return rect_pos

rects = []

while True:
    rect = Vec2(random.randint(1, 100), random.randint(1, 100))
    rects.append((add(rect), rect))
    img.show()
    input()
