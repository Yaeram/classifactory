"""Основной файл программы."""
import json
import logging
import os
import re
import sys
from collections import Counter
from time import sleep

import requests
from bs4 import BeautifulSoup
from nltk import SnowballStemmer  # pylint: disable=no-name-in-module
from pkg_resources import resource_filename


def pkgfile(path) -> str:
    """Получить путь к файлу пакета."""
    tpath = os.path.curdir
    return os.path.abspath(tpath + '/' + path)


# Логирование
LOGFORMAT = "%(asctime)s.%(msecs)03d - [%(levelname)s] - " + \
            "(%(filename)s).%(funcName)s - %(message)s"
log = logging.getLogger('log')
log.propagate = False
log.setLevel(logging.INFO)
logFile = logging.FileHandler(filename=pkgfile('../textanalysis.log'))
logFormat = logging.Formatter(fmt=LOGFORMAT, datefmt='%d-%m-%Y %H:%M:%S')
logFile.setFormatter(logFormat)
log.addHandler(logFile)


class Singleton(type):
    """Метакласс обеспечивающий создание единственного экземпляра объекта."""
    _instance = None

    def __call__(cls, *args, **kwargs):
        """Работа метакласса."""
        if cls._instance is None:
            cls._instance = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class Analysis(metaclass=Singleton):
    """Объект приложения."""

    def __init__(self, themeFilePath):
        """Создание объекта."""
        log.debug('Creating object')
        self.wordsOccurences = ''
        # Файл с темами
        self.themesFile = themeFilePath
        # Загрузка алгоритмического стеммера
        self.spellchecker = SnowballStemmer("russian")
        # Проверка и чтение файла с темами
        self.checkThemesFile()
        with open(self.themesFile, encoding="utf-8") as file:
            self.themes = json.load(file)
            log.debug('Themes imported to JSON')

    def checkThemesFile(self):
        """Проверяем файл для хранения тем."""
        # Если не существует файла с темами или пустой...
        log.debug('Checking themes file')
        if not os.path.exists(self.themesFile) or \
                os.stat(self.themesFile).st_size == 0:
            log.warning('Themes file empty or not found. Creating new')
            # То записываем {}
            with open(self.themesFile, "w", encoding="utf-8") as file:
                file.write("{}")
        log.debug('Themes file is valid')
        return 0

    def getThemesFormatted(self):
        """Красивый вывод всех тем."""
        log.debug('Printing themes to console')
        if len(self.themes.keys()) == 0:
            log.warning('Themes file is empty')
            return "Список тем пуст!"
        answer = "Темы:\n"
        for index, keys in enumerate(self.themes.keys()):
            # i) Название_темы
            answer += str(index + 1) + ") " + str(keys).title() + "\n"
        return answer

    def parseKeyWords(self, theme):
        """Поиск ключевых слов по теме в интернете."""
        theme = theme.lower()
        # Получение содержимого сайта
        link = "https://www.bukvarix.com/keywords/?q="
        log.info(f'Getting data from {link + theme}')
        page = BeautifulSoup(
            requests.get(
                link + theme,
                timeout=30)
            .text,
            "html.parser"
        )
        # Получение ключевых слов
        try:
            rawKeyWords = re.findall(
                r'"([\w ]+)"', str(re.findall(r'"data":([\w \S]+)', str(page))[0]))
        except IndexError:
            log.info("Failed to get data. Waiting")
            print('Не удалось получить слова. Ожидание 3 секунды')
            sleep(3)
            return self.parseKeyWords(theme)
        # Обработка ключевых слов
        log.debug(f'Got {len(rawKeyWords)} entries from link')
        keyWords = []
        for elem in rawKeyWords:
            for word in elem.split(' '):
                word = word.lower()
                if word != theme and not any(char.isdigit() for char in word):
                    keyWords.append(word)
        log.info(
            f'Collected key words array for {theme}. Length {len(keyWords)}')
        return keyWords

    def keyWordsArrayWorker(self, array):
        """Работа со списком ключевых слов.

        Добавляет стемы, убирает повторы и сортирует список.
        """
        log.debug(
            f'Array length: {len(array)}. Removing dupes')
        # Убираем повторы
        array = list(set(array))
        log.debug(
            f'Array length: {len(array)}. Adding stems')
        # Добавляем стемы для каждого слова
        arrayLength = len(array)
        for i in range(arrayLength):  # pylint: disable=unused-variable
            word = array.pop(0)
            stems = self.spellchecker.stem(word)
            if stems:
                array += [stems]
            else:
                # У слова нет стема, возвращаем его в список
                array += [word]
        # Убираем повторы
        log.debug(
            f'Array length: {len(array)}. Removing dupes and sorting')
        array = list(set(array))
        # Сортируем
        array.sort()
        log.debug(f"Final array length: {len(array)}")
        return array

    def addTheme(self, theme):
        """Добавление темы в программу."""
        log.info(f"Adding theme {theme}")
        if self.themes.get(theme) is not None:
            log.warning('Theme already exist')
            return "Тема " + theme + " уже существует!"


        # Нарушена грамматика названия темы
        # if self.spellchecker.spell(theme) is False:
        #     log.warning('Theme failed spell check')
        #     print("Тема " + theme + " отклонена: некорректное слово!")
        #     return 2

        # Убрать дубликаты
        log.info('Getting key words for theme')
        self.themes[theme] = self.keyWordsArrayWorker(
            self.parseKeyWords(theme) + [theme])
        self.saveThemes()
        return "Тема " + theme + " успешно добавлена!"


    def removeTheme(self, theme):
        """Удаление темы из программы."""
        log.info(f"Removing theme {theme}")
        # Если нет темы
        if self.themes.get(theme) is None:
            log.warning("Theme does not exist")
            return "Тема " + theme + " не существует!"
        # Убираем тему
        self.themes.pop(theme)
        self.saveThemes()
        return "Тема " + theme + " удалена!"

    def parseStringText(self, text):
        """Разделение текста на слова и сохранение частоты появления."""
        log.debug("Splitting text")
        # Разделение слов в тексте
        words = re.split('[^a-zа-яё]+', text, flags=re.IGNORECASE)
        self.wordsOccurences = self.countWordsFromText(words)
        return 0

    def parseTextFile(self, inputFile):
        """Получение текста из файла."""
        log.info(f"Reading file {inputFile}")
        with open(inputFile, "r", encoding="utf-8") as file:
            self.parseStringText(file.read())
        return 0

    def countWordsFromText(self, words):
        """Подсчет слов в тексте и конвертация слов в стемы."""
        log.info("Counting words")
        # Стемминг (забираем слово и добавляем его основу - стем)
        wordsLen = len(words)
        log.debug(f"Words array lenght: {wordsLen}")
        log.info("Converting words to stems if possible")
        for i in range(wordsLen):  # pylint: disable=unused-variable
            word = words.pop(0)
            stems = self.spellchecker.stem(word)
            # if stems: words +=  list(map(lambda x: x.decode('utf-8'), stems))
            # Добавляем один стем чтобы не удваивать вероятность
            if isinstance(stems, list) and stems:
                words += [stems[0].decode('utf-8')]
            else:
                # У слова нет стема, возвращаем его в список
                words += [word]
        # Подсчет кол-ва слов
        log.debug(f"Words array lenght: {wordsLen}")
        return Counter(words)

    def findCoincidences(self):
        """Поиск совпадений текста с ключевыми словами тем."""
        log.info('Finding occurences in key words dictionary')
        wordsOccurences = self.wordsOccurences
        counts = []  # Счетчик слов для каждой темы

        # Проходим по ключевым словам тем
        log.debug(f"Themes array length: {len(self.themes.values())}")
        for keyWords in self.themes.values():
            themeCount = []  # Счетчик слов темы
            for word in keyWords:
                # Слово из текста есть в ключевых словах
                wordCount = wordsOccurences.get(word)
                if wordCount is not None:
                    themeCount.append(wordCount)
            counts.append(sum(themeCount))
            log.debug(
                f"Matching occurences for theme {list(self.themes.keys())[len(counts) - 1]}" +
                f" - {sum(themeCount)} matches")
        countsAll = sum(counts)  # Всего слов которые нашлись в темах
        log.info(F"Occurences array: {', '.join(map(str, counts))}")
        log.info(F"Total occuences: {countsAll}")
        # Возврат: тема - процент слов
        themesList = list(self.themes.keys())
        result = {themesList[i]: round(counts[i] / countsAll * 100, 2)
                  for i in range(len(themesList))}
        log.info(f"Percentages: {', '.join(map(str, result.values()))}")
        return result

    def checkText(self):
        """Проверка текста.

        Запуск алгоритма, а затем вывод информации к какой теме
        относится текст и с какой вероятностью.
        """
        # Алгоритм
        localdata = self.findCoincidences()
        # Вывод
        textTheme = max(localdata, key=localdata.get).title()
        log.info(
            f"Text theme: {textTheme} with percentage of {localdata.get(textTheme)}")
        log.info("Printing percentages")
        answer = "\nТема текста: " + textTheme + "\n\n"
        answer += "Общая вероятность по всем темам:\n"
        for key, value in localdata.items():
            answer += "Тема: " + key.title() + " - " + str(value) + "%" + "\n"
        return answer

    def saveThemes(self):
        """Сохранить данные из оперативной памяти в файл тем в конце работы."""
        log.debug("Updating theme file")
        with open(self.themesFile, "w", encoding="utf-8") as themeFile:
            text = json.dumps(self.themes, ensure_ascii=False)
            themeFile.write(text)

    def __del__(self):
        """Деструктор объекта."""
        log.debug("Object removed")


def main(args):
    """Основа приложения.

    Определяет режим работы.
    """
    log.info('Program started')
    # Флаг использования файлов по умолчанию
    pkgFilesFlag = args['use_local_files']
    # Если не указан файл с темами то используем встроенный
    if pkgFilesFlag in (1, 3):
        themesFile = pkgfile(args['--themes_file'])
    else:
        themesFile = args['--themes_file']

    log.info(f'Using themes file {themesFile}')
    # Объект приложения
    obj = Analysis(themesFile)
    log.debug('Base object created')
    # Добавление темы
    if args['add']:
        return obj.addTheme(args['<theme>'])

    # Удаление темы
    elif args['remove']:
        return obj.removeTheme(args['<theme>'])

    # Вывод списка тем
    elif args['list']:
        return obj.getThemesFormatted()

    # Обработка текста
    elif args['text']:
        obj.parseStringText(args['<text>'])
        result = obj.checkText()
        log.info('Program finished work')
        return result

    # Обработка файла
    else:
        # Если не указан файл с текстом то используем пример
        if pkgFilesFlag in (2, 3):
            inputFile = pkgfile(args['--input_file'])
        else:
            inputFile = args['--input_file']
        # Если не существует файла с текстом то выходим
        if not os.path.exists(inputFile):
            log.error(f"Input file not found. Filename:{inputFile}")
            print('Файла с текстом не существует')
            sys.exit()
        obj.parseTextFile(inputFile)
        result = obj.checkText()
        log.info('Program finished work')
        return result
    log.info('Program finished work')
    return 0


if __name__ == "__main__":
    print("Запуск производится только из __main__")
