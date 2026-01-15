from Engine import Vec2

atlas_size = Vec2(512, 512)

class Packer:
    def __init__(self):
        self.available = [(Vec2(), atlas_size.copy())]

    def add(self, size):
        for i, [pos, maxsize] in enumerate(self.available):
            if maxsize.lt_or(size):  # maxsize.x < size.x or maxsize.y < size.y
                continue
            print(pos, maxsize)
            self.available.pop(i)
            # paste
            tr = (pos + size.vx, maxsize - size.vx)  # TR
            bl = (pos + size.vy, maxsize - size.vy)  # BL
            rect_pos = pos
            break
        else:
            print("No place found")
            raise RuntimeError
        # update maxsize
        for pos, maxsize in self.available:
            if pos.ge_or(rect_pos + size) or rect_pos.ge_or(pos + maxsize):
                continue
            if pos.y < rect_pos.y:
                maxsize.y = rect_pos.y - pos.y
            if pos.x < rect_pos.x:
                maxsize.x = rect_pos.x - pos.x

        self.available.extend((tr, bl))
        self.available.sort(key=lambda key: key[0].x * 512 + key[0].y)

        print(size, rect_pos)
        return rect_pos
