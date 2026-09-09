"""
Наполняет trainer_tasks стартовым банком заданий по темам ОГЭ (математика —
все 7 тем из отчёта тестирования ИИ-ассистента; русский язык — базовый набор).
Идемпотентно: пропускает задания, которые уже есть в БД (сверка по
subject+question), так что скрипт безопасно перезапускать.

Контент — типовые школьные задачи в стиле ОГЭ, все ответы вычислены и
проверены при подготовке. Это стартовый набор для тестов и первой беты,
не официальный банк ФИПИ — перед показом реальным ученикам стоит, чтобы
кто-то из команды с педагогическим бэкграундом (например, Валерия) пробежался
глазами по формулировкам.

Запуск: python -m app.seed_tasks
"""
import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.trainer import TrainerTask

MATH_TASKS = [
    # --- Уравнения ---
    dict(subject="math", topic="Уравнения", difficulty=1,
         question="Решите уравнение: 3x - 7 = 14",
         options=None, correct_answer="7",
         explanation="Перенесите -7 в правую часть с обратным знаком: 3x = 21. "
                      "Разделите обе части на 3: x = 7."),
    dict(subject="math", topic="Уравнения", difficulty=1,
         question="Решите уравнение: 5x + 2 = 3x - 8",
         options=None, correct_answer="-5",
         explanation="Перенесите слагаемые с x влево, числа вправо: 2x = -10. "
                      "Разделите на 2: x = -5."),
    dict(subject="math", topic="Уравнения", difficulty=1,
         question="Решите уравнение: 2(3x - 4) = 10",
         options=None, correct_answer="3",
         explanation="Раскройте скобки: 6x - 8 = 10. Перенесите -8: 6x = 18. x = 3."),
    dict(subject="math", topic="Уравнения", difficulty=2,
         question="Решите уравнение: x² - 9 = 0 (в ответе укажите положительный корень)",
         options=None, correct_answer="3",
         explanation="x² = 9, значит x = 3 или x = -3. Положительный корень: 3."),
    dict(subject="math", topic="Уравнения", difficulty=2,
         question="Решите уравнение: x² - 5x + 6 = 0 (в ответе укажите меньший корень)",
         options=None, correct_answer="2",
         explanation="По теореме Виета: x1 + x2 = 5, x1 * x2 = 6 → корни 2 и 3. "
                      "Меньший корень: 2."),
    dict(subject="math", topic="Уравнения", difficulty=2,
         question="Решите уравнение: (x-3)(x+5) = 0 (в ответе укажите меньший корень)",
         options=None, correct_answer="-5",
         explanation="Произведение равно нулю, если один из множителей равен нулю: "
                      "x = 3 или x = -5. Меньший корень: -5."),
    dict(subject="math", topic="Уравнения", difficulty=2,
         question="Решите уравнение: x/3 + x/4 = 7",
         options=None, correct_answer="12",
         explanation="Приведите к общему знаменателю 12: 4x/12 + 3x/12 = 7 → 7x = 84 → x = 12."),

    # --- Проценты ---
    dict(subject="math", topic="Проценты", difficulty=1,
         question="Найдите 15% от числа 200",
         options=None, correct_answer="30",
         explanation="15% от числа = число * 0.15. 200 * 0.15 = 30."),
    dict(subject="math", topic="Проценты", difficulty=2,
         question="Цену товара снизили с 500 до 400 рублей. На сколько процентов снизилась цена?",
         options=None, correct_answer="20",
         explanation="Снижение = 500 - 400 = 100 рублей. Это 100/500 * 100% = 20% от исходной цены."),
    dict(subject="math", topic="Проценты", difficulty=2,
         question="Число увеличили на 20% и получили 120. Найдите исходное число",
         options=None, correct_answer="100",
         explanation="Если x — исходное число, то x * 1.2 = 120, значит x = 120 / 1.2 = 100."),
    dict(subject="math", topic="Проценты", difficulty=1,
         question="Вкладчик положил в банк 10000 рублей под 10% годовых. Сколько будет на счету через год?",
         options=None, correct_answer="11000",
         explanation="10000 + 10% от 10000 = 10000 + 1000 = 11000 рублей."),
    dict(subject="math", topic="Проценты", difficulty=2,
         question="Найдите число, если 30% его равны 90",
         options=None, correct_answer="300",
         explanation="Если x — искомое число, то 0.3x = 90, значит x = 90 / 0.3 = 300."),

    # --- Неравенства ---
    dict(subject="math", topic="Неравенства", difficulty=2,
         question="Решите неравенство: 2x - 3 > 5 (в ответе укажите наименьшее целое решение)",
         options=None, correct_answer="5",
         explanation="2x > 8 → x > 4. Наименьшее целое число, большее 4, — это 5."),
    dict(subject="math", topic="Неравенства", difficulty=1,
         question="Решите неравенство: 3x + 1 ≤ 10 (в ответе укажите наибольшее целое решение)",
         options=None, correct_answer="3",
         explanation="3x ≤ 9 → x ≤ 3. Наибольшее целое решение: 3."),
    dict(subject="math", topic="Неравенства", difficulty=2,
         question="Решите неравенство: -2x + 4 > 0 (в ответе укажите наибольшее целое решение)",
         options=None, correct_answer="1",
         explanation="-2x > -4 → x < 2 (знак меняется при делении на отрицательное число). "
                      "Наибольшее целое число, меньшее 2, — это 1."),
    dict(subject="math", topic="Неравенства", difficulty=2,
         question="Решите неравенство: x² ≤ 16 (в ответе укажите наибольшее целое решение)",
         options=None, correct_answer="4",
         explanation="Неравенству удовлетворяют x от -4 до 4 включительно. Наибольшее целое: 4."),
    dict(subject="math", topic="Неравенства", difficulty=1,
         question="Решите неравенство: 5 - x ≥ 2 (в ответе укажите наибольшее целое решение)",
         options=None, correct_answer="3",
         explanation="-x ≥ -3 → x ≤ 3 (знак меняется при делении на отрицательное число). "
                      "Наибольшее целое решение: 3."),

    # --- Системы уравнений ---
    dict(subject="math", topic="Системы", difficulty=2,
         question="Решите систему: x + y = 10, x - y = 2 (в ответе укажите x)",
         options=None, correct_answer="6",
         explanation="Сложите уравнения: 2x = 12 → x = 6."),
    dict(subject="math", topic="Системы", difficulty=2,
         question="Решите систему: 2x + y = 7, x = y + 2 (в ответе укажите x)",
         options=None, correct_answer="3",
         explanation="Подставьте x = y+2 в первое уравнение: 2(y+2) + y = 7 → 3y = 3 → y = 1, x = 3."),
    dict(subject="math", topic="Системы", difficulty=2,
         question="Решите систему: x + 2y = 8, x - y = 2 (в ответе укажите y)",
         options=None, correct_answer="2",
         explanation="Вычтите второе уравнение из первого: 3y = 6 → y = 2."),
    dict(subject="math", topic="Системы", difficulty=2,
         question="Решите систему: 3x - y = 5, x + y = 7 (в ответе укажите y)",
         options=None, correct_answer="4",
         explanation="Сложите уравнения: 4x = 12 → x = 3. Тогда y = 7 - 3 = 4."),
    dict(subject="math", topic="Системы", difficulty=1,
         question="Решите систему: x = 2y, x + y = 9 (в ответе укажите x)",
         options=None, correct_answer="6",
         explanation="Подставьте x = 2y: 2y + y = 9 → y = 3, x = 2*3 = 6."),

    # --- Вероятность ---
    dict(subject="math", topic="Вероятность", difficulty=1,
         question="Монету подбрасывают один раз. Найдите вероятность выпадения орла",
         options=None, correct_answer="0.5",
         explanation="Всего 2 равновозможных исхода (орёл, решка), благоприятный — 1. P = 1/2 = 0.5."),
    dict(subject="math", topic="Вероятность", difficulty=1,
         question="В коробке 10 шаров: 4 красных и 6 синих. Найдите вероятность того, что "
                    "наугад взятый шар окажется красным",
         options=None, correct_answer="0.4",
         explanation="P = число благоприятных исходов / общее число исходов = 4/10 = 0.4."),
    dict(subject="math", topic="Вероятность", difficulty=1,
         question="Игральный кубик бросают один раз. Найдите вероятность выпадения чётного числа очков",
         options=None, correct_answer="0.5",
         explanation="Чётные числа на кубике: 2, 4, 6 — 3 из 6 граней. P = 3/6 = 0.5."),
    dict(subject="math", topic="Вероятность", difficulty=2,
         question="В классе 25 учеников, из них 15 девочек. Случайно выбирают одного ученика. "
                    "Найдите вероятность, что это мальчик",
         options=None, correct_answer="0.4",
         explanation="Мальчиков 25 - 15 = 10. P = 10/25 = 0.4."),
    dict(subject="math", topic="Вероятность", difficulty=2,
         question="Вероятность того, что новый чайник прослужит больше года, равна 0.94. "
                    "Найдите вероятность, что он сломается в течение первого года",
         options=None, correct_answer="0.06",
         explanation="События противоположны, сумма их вероятностей равна 1: P = 1 - 0.94 = 0.06."),

    # --- Прогрессии ---
    dict(subject="math", topic="Прогрессии", difficulty=2,
         question="Арифметическая прогрессия: a1 = 3, d = 4. Найдите a5",
         options=None, correct_answer="19",
         explanation="Формула n-го члена: an = a1 + d(n-1). a5 = 3 + 4*4 = 19."),
    dict(subject="math", topic="Прогрессии", difficulty=2,
         question="Дана арифметическая прогрессия: 2, 5, 8, 11, ... Найдите 10-й член",
         options=None, correct_answer="29",
         explanation="a1 = 2, d = 3. a10 = 2 + 3*9 = 29."),
    dict(subject="math", topic="Прогрессии", difficulty=2,
         question="Геометрическая прогрессия: b1 = 2, q = 3. Найдите b4",
         options=None, correct_answer="54",
         explanation="Формула n-го члена: bn = b1 * q^(n-1). b4 = 2 * 3³ = 2 * 27 = 54."),
    dict(subject="math", topic="Прогрессии", difficulty=1,
         question="Найдите сумму первых пяти членов арифметической прогрессии: 1, 3, 5, 7, 9",
         options=None, correct_answer="25",
         explanation="1 + 3 + 5 + 7 + 9 = 25."),
    dict(subject="math", topic="Прогрессии", difficulty=2,
         question="Геометрическая прогрессия: 1, 2, 4, 8, ... Найдите 6-й член",
         options=None, correct_answer="32",
         explanation="b1 = 1, q = 2. b6 = 1 * 2⁵ = 32."),

    # --- Функции ---
    dict(subject="math", topic="Функции", difficulty=1,
         question="Дана функция y = 2x + 3. Найдите y при x = 5",
         options=None, correct_answer="13",
         explanation="Подставьте x = 5: y = 2*5 + 3 = 13."),
    dict(subject="math", topic="Функции", difficulty=1,
         question="Дана функция y = x² - 1. Найдите y при x = -3",
         options=None, correct_answer="8",
         explanation="Подставьте x = -3: y = (-3)² - 1 = 9 - 1 = 8."),
    dict(subject="math", topic="Функции", difficulty=2,
         question="График функции y = kx проходит через точку (2, 6). Найдите k",
         options=None, correct_answer="3",
         explanation="Подставьте координаты точки: 6 = k*2, значит k = 3."),
    dict(subject="math", topic="Функции", difficulty=1,
         question="Найдите нуль функции y = x - 4 (значение x, при котором y = 0)",
         options=None, correct_answer="4",
         explanation="Решите уравнение x - 4 = 0: x = 4."),
    dict(subject="math", topic="Функции", difficulty=2,
         question="Дана функция y = 3x - 7. При каком x значение функции равно 5?",
         options=None, correct_answer="4",
         explanation="Решите уравнение 3x - 7 = 5: 3x = 12, x = 4."),
]

RUSSIAN_TASKS = [
    dict(subject="russian", topic="Орфография", difficulty=2,
         question="Какая буква пропущена в слове «бе..полезный» — приставка перед глухим согласным?",
         options=["с", "з"], correct_answer="с",
         explanation="Приставки на З/С: перед глухим согласным (П) пишется С — «бесполезный»."),
    dict(subject="russian", topic="Орфография", difficulty=2,
         question="Как пишется «(не)большой дом» в значении «маленький» — слитно или раздельно?",
         options=["слитно", "раздельно"], correct_answer="слитно",
         explanation="Если «не» можно заменить синонимом без «не» (маленький) и нет "
                      "противопоставления с союзом «а», прилагательное с «не» пишется слитно."),
    dict(subject="russian", topic="Орфография", difficulty=2,
         question="Какая буква пишется в корне слова «прил..жение» перед буквой Ж?",
         options=["о", "а"], correct_answer="о",
         explanation="Корень -лаг-/-лож-: перед Ж пишется О («приложение»), перед Г — А («прилагать»)."),
    dict(subject="russian", topic="Морфология", difficulty=1,
         question="Определите часть речи слова «быстро» в предложении «Он бежал быстро»",
         options=["наречие", "прилагательное", "глагол"], correct_answer="наречие",
         explanation="Слово отвечает на вопрос «как?» и обозначает признак действия — это наречие."),
    dict(subject="russian", topic="Морфология", difficulty=2,
         question="Определите часть речи слова «бегущий» в словосочетании «бегущий человек»",
         options=["причастие", "деепричастие", "глагол"], correct_answer="причастие",
         explanation="«Бегущий» обозначает признак предмета по действию и отвечает на вопрос "
                      "«какой?» — это причастие."),
    dict(subject="russian", topic="Пунктуация", difficulty=2,
         question="Нужна ли запятая перед «и» в предложении «Он читал книгу и слушал музыку»?",
         options=["нет", "да"], correct_answer="нет",
         explanation="«И» соединяет однородные сказуемые без повтора союза — запятая не нужна."),
    dict(subject="russian", topic="Фонетика", difficulty=3,
         question="Сколько звуков в слове «яблоко»?",
         options=None, correct_answer="7",
         explanation="Буква Я в начале слова даёт два звука [й] и [а]. Всего: й-а-б-л-о-к-о = 7 звуков "
                      "(при 6 буквах)."),
    dict(subject="russian", topic="Фонетика", difficulty=1,
         question="Сколько букв в слове «яблоко»?",
         options=None, correct_answer="6",
         explanation="я-б-л-о-к-о — 6 букв."),
]

ALL_TASKS = MATH_TASKS + RUSSIAN_TASKS


async def seed():
    async with AsyncSessionLocal() as db:
        existing = set(
            (await db.execute(select(TrainerTask.subject, TrainerTask.question))).all()
        )
        added = 0
        for data in ALL_TASKS:
            key = (data["subject"], data["question"])
            if key in existing:
                continue
            db.add(TrainerTask(**data))
            added += 1
        await db.commit()
        print(f"Добавлено новых заданий: {added} (пропущено уже существующих: {len(ALL_TASKS) - added})")


if __name__ == "__main__":
    asyncio.run(seed())
