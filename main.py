from util.config import dev
from app import app


if dev:
    print('dev')
    app.run()
