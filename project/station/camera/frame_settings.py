import cv2
import numpy as np
from PIL import Image, ImageEnhance

from project.configuration.worker import read_from_json


def apply_settings_to_frame(frame):
    brightness = read_from_json(
        "project/configuration/picture.json",
        "brightness") / 50
    contrast = read_from_json(
        "project/configuration/picture.json",
        "contrast") / 50
    saturation = read_from_json(
        "project/configuration/picture.json",
        "saturation") / 50
    grain_level = read_from_json(
        "project/configuration/picture.json",
        "grain_level") / 50
    red_filter = read_from_json(
        "project/configuration/picture.json",
        "red_filter") / 100
    green_filter = read_from_json(
        "project/configuration/picture.json",
        "green_filter") / 100
    blue_filter = read_from_json(
        "project/configuration/picture.json",
        "blue_filter") / 100

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame)

    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    if contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(contrast)
    if saturation != 1.0:
        image = ImageEnhance.Color(image).enhance(saturation)
    if grain_level != 1.0:
        image = ImageEnhance.Sharpness(image).enhance(grain_level)

    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    frame = frame.astype(np.float32)
    frame[:, :, 0] *= blue_filter
    frame[:, :, 1] *= green_filter
    frame[:, :, 2] *= red_filter
    frame = np.clip(frame, 0, 255).astype(np.uint8)

    return frame
