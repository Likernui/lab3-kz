# Связь пунктов задания с функциями обработки и вариантами сравнения.

from color import binary_transform, log_transform, power_transform, slice_brightness
from sharpness import smooth_for_sharpness, unsharp_mask
from smoothing import box_filter, gaussian_filter, median_filter, sigma_filter


COLOR = "1. Цветность"
SMOOTHING = "2. Сглаживание"
SHARPNESS = "3. Резкость"
FILTERS = ("Прямоугольный", "Медианный", "Гаусса", "Сигма")
MODES = {
    COLOR: ("Логарифм", "Степенное", "Бинарное", "Диапазон: константа", "Диапазон: сохранить"),
    SMOOTHING: FILTERS,
    SHARPNESS: ("Все фильтры",) + FILTERS,
}

# Поле: (подпись, начальное значение, тип числа).
FIELDS = {
    (COLOR, "Логарифм"): (),
    (COLOR, "Степенное"): (("Гамма > 0", "0.5", float),),
    (COLOR, "Бинарное"): (("Порог 0..255", "128", int),),
    (COLOR, "Диапазон: константа"): (
        ("Нижняя граница", "80", int),
        ("Верхняя граница", "160", int),
        ("Вне диапазона", "0", int),
    ),
    (COLOR, "Диапазон: сохранить"): (
        ("Нижняя граница", "80", int),
        ("Верхняя граница", "160", int),
    ),
    (SMOOTHING, "Прямоугольный"): (("Размеры 3 или 5", "3,5", int),),
    (SMOOTHING, "Медианный"): (("Размеры 3 или 5", "3,5", int),),
    (SMOOTHING, "Гаусса"): (("σ > 0", "0.5,1,2", float),),
    (SMOOTHING, "Сигма"): (
        ("Размеры от 5", "5", int),
        ("σ > 0", "20,40,60", float),
    ),
    (SHARPNESS, "Все фильтры"): (
        ("λ > 0", "0.5,1.5", float),
        ("σ сигма-фильтра", "30", float),
    ),
    (SHARPNESS, "Прямоугольный"): (("k (размер 2k+1)", "1,2", int), ("λ > 0", "0.5,1.5", float)),
    (SHARPNESS, "Медианный"): (("k (размер 2k+1)", "1,2", int), ("λ > 0", "0.5,1.5", float)),
    (SHARPNESS, "Гаусса"): (("k (размер 2k+1)", "1,2", int), ("λ > 0", "0.5,1.5", float)),
    (SHARPNESS, "Сигма"): (
        ("k (размер 2k+1)", "2,3", int),
        ("λ > 0", "0.5,1.5", float),
        ("σ сигма-фильтра", "30", float),
    ),
}
HINTS = {
    COLOR: "Диапазон яркостей выделяется белым; вне его пиксели заменяются или сохраняются.",
    SMOOTHING: "Несколько значений разделяйте запятыми. Карта разности показывает изменение яркости.",
    SHARPNESS: "Резкость: J = I + λ(I − S). Для каждого k можно сравнить несколько λ.",
}


def _one(parameters, index):
    # Взять единственное значение из поля, где список не нужен.
    values = parameters[index]
    if len(values) != 1:
        raise ValueError("В этом поле укажите одно число.")
    return values[0]


def make_variants(image, mode, operation, parameters):
    # Вернуть пары (название, изображение) для выбранного пункта.
    if mode == COLOR:
        return _color_variants(image, operation, parameters)
    if mode == SMOOTHING:
        return _smoothing_variants(image, operation, parameters)
    if mode == SHARPNESS:
        return _sharpness_variants(image, operation, parameters)
    raise ValueError("Неизвестный пункт задания.")


def _color_variants(image, operation, parameters):
    # Пункт 1: один результат для выбранного преобразования яркости.
    if operation == "Логарифм":
        return [("1.1 Логарифм", log_transform(image))]
    if operation == "Степенное":
        gamma = _one(parameters, 0)
        return [(f"1.2 Степенное γ={gamma:g}", power_transform(image, gamma))]
    if operation == "Бинарное":
        threshold = _one(parameters, 0)
        return [(f"1.3 Порог {threshold}", binary_transform(image, threshold))]

    low, high = _one(parameters, 0), _one(parameters, 1)
    if operation == "Диапазон: константа":
        constant = _one(parameters, 2)
        result = slice_brightness(image, low, high, "constant", constant)
        return [(f"1.4 Диапазон {low}..{high}, вне={constant}", result)]
    if operation == "Диапазон: сохранить":
        result = slice_brightness(image, low, high, "keep")
        return [(f"1.4 Диапазон {low}..{high}, вне=исходное", result)]
    raise ValueError("Неизвестное преобразование яркости.")


def _smoothing_variants(image, operation, parameters):
    # Пункт 2: результаты для каждого введённого размера или σ.
    variants = []
    if operation in ("Прямоугольный", "Медианный"):
        for size in parameters[0]:
            if operation == "Прямоугольный":
                result = box_filter(image, size)
            else:
                result = median_filter(image, size)
            title = f"2.1 {operation} {size}×{size}"
            variants.append((title, result))
    elif operation == "Гаусса":
        for sigma in parameters[0]:
            variants.append((f"2.2 Гаусса σ={sigma:g}", gaussian_filter(image, sigma)))
    elif operation == "Сигма":
        for size in parameters[0]:
            for sigma in parameters[1]:
                title = f"2.3 Сигма {size}×{size}, σ={sigma:g}"
                variants.append((title, sigma_filter(image, size, sigma)))
    else:
        raise ValueError("Неизвестный фильтр сглаживания.")
    return variants


def _sharpness_variants(image, operation, parameters):
    # Пункт 3: сочетания фильтра, радиуса k и коэффициента λ.
    if operation == "Все фильтры":
        # Для сигма-фильтра k начинается с 2, как требует лекция.
        lambda_values = parameters[0]
        sigma = _one(parameters, 1)
        pairs = []
        for filter_name in FILTERS:
            if filter_name == "Сигма":
                k_values = (2, 3)
            else:
                k_values = (1, 2)
            for k in k_values:
                pairs.append((filter_name, k))
    elif operation in FILTERS:
        lambda_values = parameters[1]
        if operation == "Сигма":
            sigma = _one(parameters, 2)
        else:
            sigma = 30
        pairs = []
        for k in parameters[0]:
            pairs.append((operation, k))
    else:
        raise ValueError("Неизвестный фильтр для повышения резкости.")
    for lambda_value in lambda_values:
        if lambda_value <= 0:
            raise ValueError("λ должна быть больше нуля.")

    variants = []
    for filter_name, k in pairs:
        # Сглаживание считаем один раз на каждый k, затем пробуем все λ.
        smoothed = smooth_for_sharpness(image, filter_name, 2 * k + 1, sigma)
        for lambda_value in lambda_values:
            result = unsharp_mask(image, smoothed, lambda_value)
            title = f"3 {filter_name}, k={k}, λ={lambda_value:g}"
            variants.append((title, result))
    return variants
