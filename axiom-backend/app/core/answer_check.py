def normalize_answer(raw: str) -> str:
    """Приводит ответ к сравнимому виду: убирает пробелы, унифицирует
    десятичный разделитель (запятая -> точка), приводит к нижнему регистру.
    Для чисел вида '2.50' и '2.5' считает их равными."""
    value = raw.strip().lower().replace(",", ".").replace(" ", "")
    try:
        num = float(value)
        # избавляемся от лишних нулей: 2.50 -> 2.5, 3.0 -> 3
        return ("%g" % num)
    except ValueError:
        return value


def answers_match(submitted: str, correct: str) -> bool:
    return normalize_answer(submitted) == normalize_answer(correct)
