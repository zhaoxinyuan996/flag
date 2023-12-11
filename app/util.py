from flask import request
from util.database import build_model


def parse(model):
    return build_model(model, None, request.json)
