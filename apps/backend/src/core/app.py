__all__ = (
    'CoreApp',
)
import logging
from fastapi import FastAPI
from ..routes import eventhub, core


class CoreApp(
    FastAPI
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_logging(self, development=False):
        if development:
            logging.basicConfig(
                level=logging.INFO,
                format="[%(levelname)s]     [%(asctime)s] [%(name)s] %(message)s",
            )

        logger = logging.getLogger("src")
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    def register_routes(self):
        """라우트를 일괄 등록한다."""
        self.include_router(core.router, tags=["Chat"])
        self.include_router(eventhub.router, prefix="/eventhub", tags=["Cloud"])

