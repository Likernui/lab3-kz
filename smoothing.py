# Пункт 2: фильтры сглаживания и карта абсолютной разности.

import math

from PIL import Image


def _neighbors(pixels, width, height, x, y, radius):
    # Собираем только те соседи, которые находятся внутри изображения.
    values = []
    for ny in range(max(0, y - radius), min(height, y + radius + 1)):
        start = ny * width
        for nx in range(max(0, x - radius), min(width, x + radius + 1)):
            values.append(pixels[start + nx])
    return values


def _filter_by_window(image, size, operation, sigma=0):
    # Общий обход нужен трём фильтрам: они различаются только выбором нового значения.
    width, height = image.size
    pixels = image.tobytes()
    result = bytearray(width * height)
    radius = size // 2
    for y in range(height):
        for x in range(width):
            values = _neighbors(pixels, width, height, x, y, radius)
            if operation == "mean":
                # Прямоугольный фильтр: все соседи имеют одинаковый вес.
                value = round(sum(values) / len(values))
            elif operation == "median":
                # Медиана: центральный элемент после сортировки яркостей окна.
                values.sort()
                value = values[len(values) // 2]
            else:
                # Сигма-фильтр: берём только яркости рядом с яркостью центра.
                center = pixels[y * width + x]
                close = []
                for neighbor in values:
                    if abs(neighbor - center) <= sigma:
                        close.append(neighbor)
                # Центр всегда входит в close, поэтому список не пуст.
                value = round(sum(close) / len(close))
            result[y * width + x] = value
    return Image.frombytes("L", image.size, bytes(result))


def box_filter(image, size):
    # 2.1. Среднее в окне 3x3 или 5x5.
    if size not in (3, 5):
        raise ValueError("Для прямоугольного фильтра выберите 3 или 5.")
    return _filter_by_window(image, size, "mean")


def median_filter(image, size):
    # 2.1. Медиана в окне 3x3 или 5x5.
    if size not in (3, 5):
        raise ValueError("Для медианного фильтра выберите 3 или 5.")
    return _filter_by_window(image, size, "median")


def gaussian_size(sigma):
    # По правилу 3σ радиус примерно равен 3σ-1; округляем до целого.
    if sigma <= 0:
        raise ValueError("σ должна быть больше нуля.")
    radius = max(1, math.ceil(3 * sigma) - 1)
    size = 2 * radius + 1
    return size


def gaussian_filter(image, sigma):
    # 2.2. Гауссов фильтр: близкие к центру пиксели получают больший вес.
    size = gaussian_size(sigma)
    radius = size // 2
    width, height = image.size
    pixels = image.tobytes()
    result = bytearray(width * height)

    # Веса не зависят от позиции пикселя: рассчитываем ядро только один раз.
    weights = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            distance_squared = dx * dx + dy * dy
            weight = math.exp(-distance_squared / (2 * sigma * sigma))
            weights.append((dx, dy, weight))
    for y in range(height):
        for x in range(width):
            total = 0.0
            weight_sum = 0.0
            for dx, dy, weight in weights:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    total += pixels[ny * width + nx] * weight
                    weight_sum += weight
            # На краях делим только на сумму весов существующих соседей.
            result[y * width + x] = round(total / weight_sum)
    return Image.frombytes("L", image.size, bytes(result))


def sigma_filter(image, size, sigma):
    # 2.3. Здесь σ — допуск по яркости, а не ширина гауссова ядра.
    if size < 5 or size % 2 == 0:
        raise ValueError("Для сигма-фильтра нужен нечетный размер от 5.")
    if sigma <= 0:
        raise ValueError("σ должна быть больше нуля.")
    return _filter_by_window(image, size, "sigma", sigma)


def absolute_difference(first, second):
    # 2.4. Светлые участки карты означают большую разницу между I и S.
    if first.size != second.size:
        raise ValueError("Размеры изображений должны совпадать.")
    values = []
    for a, b in zip(first.tobytes(), second.tobytes()):
        difference = abs(a - b)
        values.append(difference)
    return Image.frombytes("L", first.size, bytes(values))
