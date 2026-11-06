# Пункт 3: повышение резкости с помощью нерезкого маскирования.

from PIL import Image

from smoothing import box_filter, gaussian_filter, median_filter, sigma_filter


def unsharp_mask(image, smoothed, lambda_value):
    # 3.1. I — исходная яркость, S — сглаженная, J — результат.
    if image.size != smoothed.size:
        raise ValueError("Размеры изображений должны совпадать.")
    if lambda_value < 0:
        raise ValueError("λ должна быть неотрицательной.")

    # Формула: J = I + λ(I - S). Ограничиваем яркость диапазоном 0..255.
    values = []
    for i, s in zip(image.tobytes(), smoothed.tobytes()):
        j = round(i + lambda_value * (i - s))
        j = max(0, min(255, j))
        values.append(j)
    return Image.frombytes("L", image.size, bytes(values))


def smooth_for_sharpness(image, filter_name, size, sigma=30):
    # Получаем S выбранным фильтром; размер окна равен 2k+1.
    if filter_name == "Прямоугольный":
        return box_filter(image, size)
    if filter_name == "Медианный":
        return median_filter(image, size)
    if filter_name == "Гаусса":
        if size not in (3, 5):
            raise ValueError("Для фильтра Гаусса выберите размер 3 или 5.")
        # Из правила 2k+1 = 6σ-1 следует σ = (size+1)/6.
        return gaussian_filter(image, (size + 1) / 6)
    if filter_name == "Сигма":
        # Здесь sigma — допустимая разница яркости с центральным пикселем.
        return sigma_filter(image, size, sigma)
    raise ValueError("Неизвестный фильтр сглаживания.")
