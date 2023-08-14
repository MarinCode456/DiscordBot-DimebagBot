# Управляет списком песен

import os
import shutil
import random

class sl:

    # Проверка существования папки
    def checkFolder(self, path):
        # Если такая папка есть, возвращает true
        return os.path.isdir(path)
    
    # Создание папки вместе с файлом list.txt
    def createFolder(self, path):
        # Создаём новую папку, а также файл list.txt, love.txt и папку notloaded
        os.mkdir(path)
        os.mkdir(path + "notloaded")
        file = open(path + "list.txt", 'w', encoding='utf-8')
        file.write("currentsong:\n\n")
        file.close()

    # Создание файла love.txt в favourites, а также папки канала
    def createLoveList(self, path):
        os.mkdir(path)
        file = open(path + "love.txt", 'w', encoding='utf-8')
        file.close()

    # По сути, генерация уникального индекса для песни
    def getSongName(self, path):
        name = self.getIndex() + ".mp3"

        # Если каким-то удивительным образом сгенерировался такой же индекс,
        # То генерируем новые до тех пор, пока их не будет в папке
        listdir = os.listdir(path)
        while name in listdir:
            name = self.getIndex() + ".mp3"

        # Возвращаем результат без .mp3
        return name[:6]
    
    def getIndex(self):
        # Вполне можно было использовать готовый модуль для создания индексов,
        # Однако я хотел попробовать сделать что-то своё

        pos1 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        pos2 = '0123456789'

        r1 = random.randint(0, len(pos1)-1); r2 = random.randint(0, len(pos2)-1)
        r3 = random.randint(0, len(pos1)-1); r4 = random.randint(0, len(pos2)-1)
        r5 = random.randint(0, len(pos1)-1); r6 = random.randint(0, len(pos2)-1)

        return pos1[r1] + pos2[r2] + pos1[r3] + pos2[r4] + pos1[r5] + pos2[r6]
    
    # Добавляет песню в конец списка
    def addSong(self, path, song_name, song_title):
        song_list = open(path + "list.txt", 'a', encoding='utf-8')
        song_list.write(song_name + ";" + song_title + '\n')
        song_list.close()

    # Добавляет песню в начало списка, нужна для команды /playnow
    def addSongToBegin(self, path, song_name, song_title):
        # Получаем весь список песен
        song_list = self.getQueueWithTitles(path)
        self.cleanSongList(path)

        list_file = open(path + "list.txt", 'a', encoding='utf-8')
        # Записываем новую песню в начало списка
        list_file.write(song_name + ";" + song_title + '\n')

        for song_with_title in song_list:
            list_file.write(song_with_title + '\n')

    # Получение списка идентификаторов песен
    def getQueue(self, path):
        song_list = []
        for line in open(path + "list.txt", 'r', encoding='utf-8'):
            # Проверка исключает добавление в список песен двух первых строк
            if (not line.startswith("currentsong")) and (line != "\n"):
                song_list.append(line.rstrip().split(";")[0])
        return song_list

    # Получение списка песен вместе с названиями
    def getQueueWithTitles(self, path):
        song_list = []
        for line in open(path + "list.txt", 'r', encoding='utf-8'):
            # Проверка исключает добавление в список песен двух первых строк
            if (not line.startswith("currentsong")) and (line != "\n"):
                song_list.append(line.rstrip())
        return song_list
    
    # Получение полного списка строчек файла list.txt (вместе со строчками currentsong)
    def getWholeQueue(self, path):
        strings = []
        for line in open(path + "list.txt", 'r', encoding='utf-8'):
            strings.append(line.rstrip())
        return strings
    
    # Обновляет список песен (new_queue - полный список вместе со строчкой currentsong)
    def updateQueue(self, path, new_queue):
        strings = ''
        for s in new_queue:
            strings = strings + s + '\n'
        
        song_list = open(path + "list.txt", 'w', encoding='utf-8')
        song_list.write(strings)
        song_list.close()

    # Создаёт папку cash, если её ещё нету
    def createCashFavouritesIfNot(self):
        if not os.path.exists(os.getcwd() + os.sep + "cash" + os.sep):
            os.mkdir("cash")
            print("[Dimebag] Папка cash успешно создана.")

        if not os.path.exists(os.getcwd() + os.sep + "favourites" + os.sep):
            os.mkdir("favourites")
            print("[Dimebag] Папка favourites успешно создана.")

    # Полностью удаляет содержимое папки cash
    def cleanAllFolders(self):
        folders = os.listdir("cash")
        cashpath = os.getcwd() + os.sep + "cash" + os.sep

        for folder in folders:
            print("        [Dimebag] Удаляем папку cash\\" + folder)
            shutil.rmtree(cashpath + folder)

    # Полностью очищает список песен по указанному пути (не удаляя строчку currentsong)
    def cleanSongList(self, path):
        song_list = open(path + "list.txt", 'w', encoding='utf-8')
        song_list.write("currentsong:\n\n")
        song_list.close()

    # Меняет строчку currentsong на пустоту
    def setNullCurrentSong(self, path):
        strings = self.getWholeQueue(path)
        strings[0] = "currentsong:"
        self.updateQueue(path, strings)

    # Проверка играет ли сейчас что-нибудь
    def currentSongExists(self, path):
        # Если в этом списке более одного элемента, значит строка хранит какую-то песню
        currentSong = self.getWholeQueue(path)[0].split(":")
        if (currentSong[1] != '') or (len(currentSong) > 2): return True
        return False
    
    # Возвращаем название текущей композиции
    def getCurrentSong(self, path):
        currentSong = self.getWholeQueue(path)[0].split(":")[1:]
        return ''.join(currentSong).split(";")[1]
    
    # Возвращает рандомную ссылку на альбом из топ 100 метал-альбомов
    def getHundredUrl(self):
        urls = []
        for url in open(os.getcwd() + os.sep + "hundred.txt", encoding='utf-8'): 
            urls.append(url.rstrip().split("[]")[1])
        return random.choice(urls)
    
    # Возвращает конкретный альбом из списка
    def getOneFromHundredUrl(self, choice):
        # Передаём именно выбор пользователя, например 100 (хотя в списке последний элемент - 99)
        choice = choice - 1 

        urls = []
        for url in open(os.getcwd() + os.sep + "hundred.txt", encoding='utf-8'): 
            urls.append(url.rstrip().split("[]")[1])
        return urls[choice]
    
    # Возвращает рандомную ссылку на избранную песню
    def getLoveUrl(self, path):
        urls = []
        for url in open(path + "love.txt", encoding='utf-8'): 
            urls.append(url.rstrip().split("[]")[1])
        return random.choice(urls)
    
    # Возвращает конкретную ссылку на песня из списка избранных
    def getOneFromLoveUrl(self, path, choice):
        # Передаём именно выбор пользователя, например 100 (хотя в списке последний элемент - 99)
        choice = choice - 1 

        urls = []
        for url in open(path + "love.txt", encoding='utf-8'): 
            urls.append(url.rstrip().split("[]")[1])
        return urls[choice]
    
    # Возвращает рандомную ссылку на одну из 30 любимых песен
    def getLikeItUrl(self):
        urls = []
        for url in open(os.getcwd() + os.sep + "likeit.txt", 'r', encoding='utf-8'): 
            urls.append(url.rstrip().split("[]")[1])
        return random.choice(urls)
    
    # Добавляет ссылку в love.txt
    def addUrlToLove(self, path, url, title):
        file = open(path + "love.txt", 'a', encoding='utf-8')
        file.write(f"{title}[]{url}\n")
        file.close()

    # Получение списка love.txt
    def getLoveList(self, path):
        love = []
        for line in open(path + "love.txt", encoding='utf-8'):
            love.append(line.rstrip())
        return love
    
    # Удаление одной песни из love.txt
    def killOneLoveSong(self, path, choice):
        # Передаём именно выбор пользователя, например 100 (хотя в списке последний элемент - 99)
        choice = choice - 1 

        loveList = self.getLoveList(path)
        deletedElement = loveList.pop(choice)

        strings = ""
        for song in loveList:
            strings += song + "\n"

        loveFile = open(path + "love.txt", 'w', encoding='utf-8')
        loveFile.write(strings)
        loveFile.close()

        # Возвращаем удалённый элемент
        return deletedElement