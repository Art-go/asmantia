from dataclasses import dataclass


@dataclass
class Texture:
    tex_id: int
    uv: tuple[int, int, int, int] #u0, v0, u1, v1
