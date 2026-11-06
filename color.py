# Пункт 1: преобразования яркости изображения в оттенках серого.

import math

from PIL import Image


def _make_image(source, values):
    # values идёт в том же порядке, что и пиксели source.
    return Image.frombytes("L", source.size, bytes(values))


def log_transform(image):
    # 1.1. Формула: s = c * ln(1 + r).
    # В режиме L каждый байт — целая яркость от 0 до 255.
    pixels: bytes = image.tobytes()
    r_max: int = max(pixels)
    if r_max == 0:
        # Для полностью чёрного изображения ln(1 + r_max) = 0.
        return image.copy()

    # Подбираем коэффициент так, чтобы самый светлый пиксель стал равен 255.
    c = 255 / math.log1p(r_max)
    new_pixels = []
    for r in pixels:
        s = round(c * math.log1p(r))
        new_pixels.append(s)
    return _make_image(image, new_pixels)


def power_transform(image, gamma):
    # 1.2. Формула: s = c * r ** gamma.
    if gamma <= 0:
        raise ValueError("Гамма должна быть больше нуля.")
    pixels: bytes = image.tobytes()
    r_max: int = max(pixels)
    if r_max == 0:
        return image.copy()

    #максимум исходного изображения переходит в 255.
    c = 255 / (r_max ** gamma)
    new_pixels = []
    for r in pixels:
        s = round(c * r ** gamma)
        # После округления яркость не должна превышать 255.
        s = min(255, s)
        new_pixels.append(s)
    return _make_image(image, new_pixels)


def binary_transform(image, threshold):
    # 1.3. Порог включён в белую часть: r >= threshold -> 255.
    if not 0 <= threshold <= 255:
        raise ValueError("Порог должен быть от 0 до 255.")
    new_pixels = []
    for r in image.tobytes():
        if r >= threshold:
            s = 255
        else:
            s = 0
        new_pixels.append(s)
    return _make_image(image, new_pixels)


def slice_brightness(image, low, high, outside="keep", constant=0):
    # 1.4. Яркости внутри [low, high] делаем белыми.
    if not 0 <= low <= high <= 255:
        raise ValueError("Границы должны быть от 0 до 255, нижняя не больше верхней.")
    if not 0 <= constant <= 255:
        raise ValueError("Константа должна быть от 0 до 255.")

    new_pixels = []
    for r in image.tobytes():
        if low <= r <= high:
            s = 255
        elif outside == "keep":
            s = r
        else:
            s = constant
        new_pixels.append(s)
    return _make_image(image, new_pixels)
