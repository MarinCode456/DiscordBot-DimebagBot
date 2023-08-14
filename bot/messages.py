import discord.ext

# Файл для хранения всех сообщений бота
class mesg:
    # Возвращает текст (embed) о том, что мы не передали url
    def playErrorEmbed(self, mention):
        textinside = f"{mention}\n" + """```Для использования команды введите:

/play <url>```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает текст (embed) об ошибке при вводе playnow
    def playnowErrorEmbed(self, mention):
        textinside = f"{mention}\n" + """```Для использования команды введите:

/playnow <url>```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает текст (embed) об ошибке при вводе hundred
    def hundredErrorEmbed(self, mention):
        textinside = f"{mention}\n" + """```Для использования команды введите:

/hundred или /hundred [1-100]```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает текст (embed) о том, что мы не подключены к каналу
    def voiceErrorEmbed(self, mention):
        textinside = f"{mention}\n" + """```Вы не подключены ни к какому из голосовых каналов!
        
Для использования команды подключитесь в любой голосовой канал.```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает текст (embed) о том, что url запрещён
    def urlErrorEmbed(self, mention):
        textinside = f"{mention}\n" + """```Данная ссылка не является разрешённой!
        
Правильная ссылка должна начинаться с:
- http://www.youtube.com
- https://www.youtube.com

Другие ссылки не поддерживаются.```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает текст (embed) о том, что не удалось скачать файл
    def downloadErrorEmbed(self, mention):
        textinside = f"{mention}\n" + """```Не удалось скачать песню.
        
Вы уверены, что верно вводите ссылку?```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает текст (embed) о том, что песня добавлена в очередь
    def addToQueueEmbed(self, mention, song_title, queue_len):
        textinside = f"{mention}\n" + f"""```{song_title} ({queue_len})```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸  Песня добавлена в очередь\n", value=textinside)
        return embed
    
    # Возвращает текст (embed) о том, что сейчас начнётся проигрывание (playnow)
    def startPlayingNowEmbed(self, mention, song_title):
        textinside = f"{mention}\n" + f"""```{song_title}```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸  Начинаю проигрывать\n", value=textinside)
        return embed
    
    # Возвращает список песен (embed)
    def getSongListEmbed(self, mention, queue, currentSongExists):
        # Если сейчас ничего не играем, то не выводим список
        if not currentSongExists:
            textinside = f"{mention}\n" + """```Сейчас ничего не играет.
            
Чтобы вывести список песен, добавьте что-нибудь в проигрывание.```"""
            embed = discord.Embed(color=discord.Colour.dark_red())
            embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
            return embed

        count = 1
        # Такие махинации, чтобы предвидеть ситуацию, когда у нас в названии песни есть символ :
        currentsong = queue[0].split(":")[1:]
        currentsong = ''.join(currentsong).split(";")[1]

        songQueue = queue[2:]

        textinside = f"{mention}\n" f"```  Текущая песня - {currentsong}\n\n"
        for song in songQueue:
            textinside += f"{count}. {song.split(';')[1]}\n"
            count += 1
        textinside += "```"

        if len(songQueue) == 0: textinside = f"{mention}\n" f"```Текущая песня - {currentsong}```"

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Ваш список песен\n", value=textinside)
        return embed
    
    # Возвращает (embed) при подключении к серверу
    def meetMeEmbed(self, server):
        textinside = f"""Сам Даймбег Даррел, великий гитарист группы Pantera спустился с небес, чтобы сыграть на сервере {server}!
        
Ниже представлен список всех моих команд:

```
/play <url>       -  Добавляет песню в плейлист проигрывания
/playnow <url>    -  Меняет текущую песню на указанную
/playlist         -  Выводит текущий плейлист
/skip             -  Пропускает текущую песню
/pause            -  Ставит воспроизведение на паузу
/clear            -  Полностью очищает плейлист
/help             -  Справка по боту

/hundred [1-100]  -  Включает случайный альбом из списка 100 лучших метал альбомов по версии Rolling Stone
/likeit           -  Включает случайную песню из списка 30 лучших песен по версии моего создателя
```
И не забывайте, я работаю только с ссылками с youtube и ни с чем другим! Только хардкор!

Топ 100 лучших метал-альбомов всех времён: [Тык](https://www.rollingstone.com/music/music-lists/the-100-greatest-metal-albums-of-all-time-113614/black-sabbath-paranoid-1970-115785/)"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Подключение к серверу!\n", value=textinside)
        return embed
    
    # Возвращает (embed) для команды /help
    def helpCommandEmbed(self, server):
        textinside = f"""Сам Даймбег Даррел, великий гитарист группы Pantera спустился с небес, чтобы сыграть на сервере {server}!
        
Ниже представлен список всех моих команд:

```
/play <url>       -  Добавляет песню в плейлист проигрывания
/playnow <url>    -  Меняет текущую песню на указанную
/playlist         -  Выводит текущий плейлист
/skip             -  Пропускает текущую песню
/pause            -  Ставит воспроизведение на паузу
/clear            -  Полностью очищает плейлист
/help             -  Справка по боту

/hundred [1-100]  -  Включает случайный альбом из списка 100 лучших метал альбомов по версии Rolling Stone
/likeit           -  Включает случайную песню из списка 30 лучших песен по версии моего создателя
```
И не забывайте, я работаю только с ссылками с youtube и ни с чем другим! Только хардкор!

Топ 100 лучших метал-альбомов всех времён: [Тык](https://www.rollingstone.com/music/music-lists/the-100-greatest-metal-albums-of-all-time-113614/black-sabbath-paranoid-1970-115785/)"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Возможности бота\n", value=textinside)
        return embed
    
    # Возвращает (embed) об успешном пропуске песни
    def skipOneSongEmbed(self, currentsong):
        textinside = f"""```{currentsong}```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Пропуск песни\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что нечего пропускать
    def nothingToSkipEmbed(self):
        textinside = f"""```В данный момент ничего не играет, а значит нечего пропускать!```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) об очистке списка песен
    def weCleanSongListEmbed(self):
        textinside = f"""```Плейлист полностью очищен.
        
Теперь вы можете начать всё с чистого листа!```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Удаление очереди\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что бот не подключен ни к какому из каналов
    def weDontHaveVoiceChannelEmbed(self):
        textinside = f"""```Бот не подключен к каналу.
        
Для использования этой команды, сначала используйте /play или /playnow для создания списка песен.```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что пользователь находится в другом канале
    def youInTheOtherChannelEmbed(self):
        textinside = f"""```Бот не подключен или подключен к другому каналу.
        
Чтобы использовать эту команду, вы должны быть в одном канале вместе с ботом.```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что нет текущей песни
    def haventCurrentSongEmbed(self):
        textinside = f"""```Я не могу поставить на паузу то, чего нет.
        
Для начала выберите песню с помощью /play или /playnow.```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что плейлист на паузе
    def playlistOnPauseEmbed(self):
        textinside = f"""```Останавливаю проигрывание```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Плейлист на паузе\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что плейлист на паузе
    def playlistKillPauseEmbed(self):
        textinside = f"""```Возобновляю проигрывание```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Плейлист снова в игре\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что в команде /hundred мы ввели что-то не то
    def hundredDigitErrorEmbed(self, mention):
        textinside = f"{mention}\n" + f"""```Чего-чего?
        
Вы уверены, что вводите число от 1 до 100?
Пример правильного ввода: /hundred 5```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что в команде /love мы ввели что-то не то
    def loveDigitErrorEmbed(self, mention, up_value):
        textinside = f"{mention}\n" + f"""```Чего-чего?
        
Вы уверены, что вводите число от 1 до {up_value}?
Пример правильного ввода: /love 1```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что в команде /loveremove мы ввели что-то не то
    def loveRemoveDigitErrorEmbed(self, mention, up_value):
        textinside = f"{mention}\n" + f"""```Чего-чего?
        
Вы уверены, что вводите число от 1 до {up_value}?
Пример правильного ввода: /loveremove 1```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что мы неправильно использовали команду /loveadd
    def noneArgsInLoveaddEmbed(self, mention):
        textinside = f"{mention}\n" + f"""```Для использования команды введите:

/loveadd <url>```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что мы неправильно использовали команду /loveremove
    def noneArgsInLoveRemoveEmbed(self, mention):
        textinside = f"{mention}\n" + f"""```Для использования команды введите:

/loveremove [номер]```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что мы неправильно использовали команду /love
    def noneArgsInLoveEmbed(self, mention):
        textinside = f"{mention}\n" + f"""```Для использования команды введите:

/love [номер]```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что мы неправильно использовали команду /loveadd
    def addToLoveErrorEmbed(self, mention):
        textinside = f"{mention}\n" + f"""```При добавлении песни в избранное произошла ошибка.
        
Напишите автору, он починит.```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что успешно добавили песню в избранное
    def successAddToLoveEmbed(self, mention, title):
        textinside = f"{mention}\n" + f"""```{title} \n\nУспешно добавлена в избранное!```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Добавление в избранное\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что у нас нет loveList
    def youHaventLoveListEmbed(self, mention):
        textinside = f"{mention}\n" + f"""```У вас нет избранных песен!
        
Чтобы их добавить используйте команду /loveadd <url>```"""

        embed = discord.Embed(colour=discord.Colour.dark_red())
        embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
        return embed
    
    # Возвращает список избранных песен (embed)
    def getLoveListEmbed(self, lovelist):
        # Если список пуст, то не выводим
        if len(lovelist) < 1:
            textinside = """```Список избранных песен этого канала пуст.
            
Вы можете добавить песни с помощью команды /loveadd <url>```"""
            embed = discord.Embed(color=discord.Colour.dark_red())
            embed.add_field(name="❌  Произошла ошибка!\n", value=textinside)
            return embed

        count = 1
        textinside = "```"
        for song in lovelist:
            title = song.split("[]")[0]
            textinside += f"{count}. {title}\n"
            count += 1
        textinside += "```"

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Ваш список избранных песен\n", value=textinside)
        return embed
    
    # Возвращает (embed) о том, что мы успешно удалили песню из избранного
    def weRemoveOneLoveSongEmbed(self, mention, title):
        textinside = f"{mention}\n" + f"""```{title} \n\nУспешно удалена из избранного!```"""

        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="🎸   Удаление из избранного\n", value=textinside)
        return embed