# pylint: disable=invalid-name
# pylint: disable=redefined-outer-name
"""Файл тестов приложения."""
import cProfile
import logging
import pstats

import pytest

from main import main, pkgfile

# Логирование дебаг сообщений
log = logging.getLogger('log')
log.setLevel(logging.DEBUG)

# Отключить логирование для более строгого профилирования
# Скрывает:
# method 'flush' of '_io.TextIOWrapper'
# logging/__init__.py:283
#
# log.setLevel(logging.CRITICAL)
#

# Сброс файла тем для тестов
with open(pkgfile('demo_data/default_themes.json'), "r", encoding="utf-8") as file:
    text = file.read()
with open(pkgfile('demo_data/test_themes.json'), "w", encoding="utf-8") as file:
    file.write(text)


@pytest.fixture
def userdata():
    """Фикстура: Входные параметры пользователя."""
    return {
        '--themes_file': './demo_data/test_themes.json',
        '--input_file': './demo_data/input.txt',
        '<text>': '',
        '<theme>': '',
        'add': False,
        'remove': False,
        'list': False,
        'text': False,
        'use_local_files': 3  # Использовать файлы по умолчанию
    }


def profile(function, *args):
    """Профилирование функции и возврат результата."""
    pr = cProfile.Profile()
    pr.enable()
    result = function(*args)
    pr.disable()
    stats = pstats.Stats(pr)
    # stats.strip_dirs()
    stats.sort_stats('tottime')
    stats.print_stats(10)
    return result


def testGenerateThemesList(userdata):
    """Добавление своих тем."""
    with open(pkgfile('demo_data/test_themes.json'), "w", encoding="utf-8") as file:
        file.write('{}')
    themes = ('Математика', 'Физика', 'Физкультура', 'Биология', 'Футбол',
              'Осень', 'Природа', 'Война')
    userdata['add'] = True
    for theme in themes:
        userdata['<theme>'] = theme
        assert main(userdata) == 0


def testRunDefault(userdata):
    """Запуск без параметров."""
    result = profile(main, userdata)
    assert result
    print("Тема: ", result)


def testRunWithString(userdata):
    """Проверка темы своего текста."""
    userdata['text'] = True
    userdata['<text>'] = 'Математика — мой любимый школьный предмет с первого класса. Мне нравится решать примеры и задачи, находить ответы на логические вопросы.'  # pylint: disable=line-too-long
    result = profile(main, userdata)
    assert result
    print("Тема: ", result)


def testAddTheme(userdata):
    """Добавление своей темы."""
    userdata['add'] = True
    userdata['<theme>'] = "Зима"
    assert profile(main, userdata) == 0


def testDeleteTheme(userdata):
    """Удаление своей темы."""
    userdata['remove'] = True
    userdata['<theme>'] = 'Зима'
    assert profile(main, userdata) == 0


def testListThemes(userdata):
    """Вывод списка тем.

    Для отображения запускать в дебаге.
    """
    userdata['list'] = True
    assert profile(main, userdata) == 0
