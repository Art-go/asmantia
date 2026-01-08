import logging

from logging_setup import setup_logging
setup_logging(logging.INFO)

import Engine
print(Engine.Vec2.down)