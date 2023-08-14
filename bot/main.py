# Программе обязательно нужен ffmpeg, установленный в PATH

import discord
import yt_dlp
import os
import asyncio
from asyncio import run
from threading import Thread

import messages
import songlist

from discord.ext import commands
from config import token

# Экземпляр класса messages для импорта сообщений бота
try:
    ms = messages.mesg()
    print("[Dimebag] Сообщения бота успешно подключены.")
except Exception as e:
    print("    *[Dimebag] Произошла ошибка при подключении сообщений!")
    print(e)

# intents - намерения для бота, указываем стандартные
try:
    intents = discord.Intents().default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)
    print("[Dimebag] Бот подключен.")
except Exception as e:
    print("    *[Dimebag] Произошла ошибка при подключении бота!")
    print(e)

# songlist - модуль, управляющий списком песен
try:
    sl = songlist.sl()
    print("[Dimebag] Библиотека управления списком песен подключена.")
except Exception as e:
    print("    *[Dimebag] Произошла ошибка при подключении обработчика списка песен!")
    print(e)

# При каждом запуске бота мы очищаем папку cash, так как там находятся все песни,
# которые мы уже проиграли и использовать не будем
try:
    sl.createCashFavouritesIfNot()
    sl.cleanAllFolders()
    print("[Dimebag] Папка cash успешно очищена.")
except Exception as e:
    print("    *[Dimebag] Произошла ошибка при очистке папки cash!")
    print(e)



# Проверка правильности введённой ссылки
def isUrlCorrect(url):
    if url.startswith("http://www.youtube.com") or url.startswith("https://www.youtube.com"):
        return True
    return False



# Библиотека асинхронная, поэтому синтаксис немного видоизменён
@bot.event
async def on_ready():
    print("[Dimebag] Успешный запуск!")

# Отправляем сообщение в первый попавшийся текстовый канал при подключении на новый сервер
@bot.event
async def on_guild_join(server):
    await server.text_channels[0].send(embed = ms.meetMeEmbed(server))

# ctx - контекст, который содержит все данные о событии
# * обозначает, что нужно нужно передавать текст, который идёт после команды
# command - текст, который идёт после команды
@bot.command()
async def play(ctx, *, command = None):
    # Добавляет песню в очередь
    author = ctx.author
    mention = ctx.author.mention

    if command == None:
        # Если после команды /play ничего не ввели
        await ctx.send(embed = ms.playErrorEmbed(mention))
        return

    params = command.split(" ")
    if len(params) > 1:
        # Параметров больше чем нужно
        await ctx.send(embed = ms.playErrorEmbed(mention))
        return
    
    # Если мы попали сюда и функция не прервалась, то всё отлично, распознаём ссылку
    url = params[0]
    server = ctx.guild

    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return
    
    # Проверка правильности введённой ссылки
    if not isUrlCorrect(url):
        await ctx.send(embed = ms.urlErrorEmbed(mention))
        return

    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)
    song_name = sl.getSongName(path)

    # Скачиваем песню
    try:
        ydl_options = {
                'format': 'bestaudio/best',
                'outtmpl': path + "notloaded" + os.sep + song_name,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }
                ],
            }

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            # Добавляем песню в очередь песен
            info = ydl.extract_info(url, download = False)
            song_title = info.get('title', None)
            sl.addSong(path, song_name, song_title)

            # Скачиваем песню в отдельном потоке
            t = Thread(target=download, args=[ydl, url, path, song_name])
            t.start()

            # Отправляем пользователю сообщение о добавлении песни в очередь
            queue_len = len(sl.getQueue(path))
            if sl.currentSongExists(path): queue_len += 1
            await ctx.send(embed = ms.addToQueueEmbed(mention, song_title, queue_len))
    except Exception as e:
        # Произошла ошибка при скачивании, возвращаем функцию
        print("    *[Dimebag] Произошла ошибка при скачивании песни " + song_name)
        print(e)
        await ctx.send(embed = ms.downloadErrorEmbed(mention))
        return
    
    # Проигрывание песни с учётом очереди
    await playSong(ctx, voice, path)

def download(ydl, url, path, song_name):
    ''' 
        Скачиваем песню в папку notloaded и как только песня докачается, перемещаем её
    в папку, которую смотрит дискорд.

        Если этого не сделать, то дискорд начнёт пытаться открыть файл, когда он ещё
    не скачан. Всё из-за специфики скачивания музыки модулем ydl - сначала создаётся
    файл-пустышка, после чего туда записывается информация.

        Если бот сразу же начнёт читать пустышку, то ydl не сможет ничего записать
    в этот файл, из-за чего никакой песни не будет, зато будет ошибка.
    '''
    ydl.download([url])
    file = path + "notloaded" + os.sep + song_name + ".mp3"
    out = path + song_name + ".mp3"
    os.replace(file, out)

async def playSong(ctx, voice, path):
    if not voice.is_playing():
        # Если ничего не играет, играем первую песню из очереди
        queue = sl.getQueue(path)
        if len(queue) == 0:
            sl.setNullCurrentSong(path)
            return
        
        # Из-за асинхронности библиотеки, подключение к войсу иногда работает неправильно
        # Например, если много раз ввести /play <url>, то фактически бот подключится к войсу только на последний
        # Введённый раз. Эта проверка помогает избежать ошибок, при этом не ломает программу и всё работает как нужно
        if not voice.is_connected():
            return

        # Если мы дошли до сюда, то список не пуст, значит нужно проиграть
        # первую песню списка, после чего удалить её из него
        song = discord.FFmpegPCMAudio(path + queue[0] + ".mp3")
        if not os.path.exists(path + queue[0] + ".mp3"):
            # Эта проверка нужна на случай, если трек ещё не успел скачаться
            print("    *[Dimebag] Система не может найти файл " + queue[0] + ".mp3" + " и пытается снова")
            await asyncio.sleep(3)
            await playSong(ctx, voice, path)
            return

        # Если мы здесь, то значит композиция найдена, начинаем проигрывание
        try:
            voice.play(song, after = lambda e: run(playSong(ctx, voice, path)))

            # Обновляем список треков, исключая проигрываемый и меняя текующую песню
            new_queue = sl.getWholeQueue(path)
            new_queue[0] = "currentsong:" + new_queue[2]
            new_queue.pop(2)
            sl.updateQueue(path, new_queue)
        except Exception as e:
            print("    *[Dimebag] Произошла ошибка при использовании функции playSong()")
            print(e)



@bot.command()
async def playnow(ctx, *, command = None):
    # Команда playnow играет песню сразу же, без каких-либо очередей,
    # А если в это время уже играет какая-то песня, то она её прерывает
    author = ctx.author
    mention = ctx.author.mention

    if command == None:
        # Если после команды /playnow ничего не ввели
        await ctx.send(embed = ms.playnowErrorEmbed(mention))
        return

    params = command.split(" ")
    if len(params) > 1:
        # Параметров больше чем нужно
        await ctx.send(embed = ms.playnowErrorEmbed(mention))
        return
    
    # Если мы попали сюда и функция не прервалась, то всё отлично, распознаём ссылку
    url = params[0]
    server = ctx.guild

    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return
    
    # Проверка правильности введённой ссылки
    if not isUrlCorrect(url):
        await ctx.send(embed = ms.urlErrorEmbed(mention))
        return

    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)
    song_name = sl.getSongName(path)

    try:
        ydl_options = {
                'format': 'bestaudio/best',
                'outtmpl': path + "notloaded" + os.sep + song_name,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }
                ],
            }

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            # Добавляем песню в начало списка
            info = ydl.extract_info(url, download = False)
            song_title = info.get('title', None)
            sl.addSongToBegin(path, song_name, song_title)

            # Скачиваем песню в отдельном потоке
            t = Thread(target=download, args=[ydl, url, path, song_name])
            t.start()

            # Отправляем пользователю сообщение о начале проигрывания новой песни
            await ctx.send(embed = ms.startPlayingNowEmbed(mention, song_title))
    except Exception as e:
        # Произошла ошибка при скачивании, возвращаем функцию
        print("*[Dimebag] Произошла ошибка при скачивании песни " + song_name)
        print(e)
        await ctx.send(embed = ms.downloadErrorEmbed(mention))
        return

    '''
        Здесь основная фишка, которую нужно понять
    Так как у нас в функции playSong записан метод after в методе play()
    То при прекращении проигрывания мы просто начинаем играть следующую песню

        Именно поэтому, чтобы не было лишней возни, мы просто сначала добавим
    Нашу новую песню в начало списка, а текущую прекратим
    В таком случае мы пропустим текущую, начнём играть следующую и не упустим список
    '''
    if voice.is_playing():
        # Если уже что-то играет, то просто пропускаем текущую песню
        voice.stop()
    else:
        # Если ничего не играет, то начинаем играть
        await playSong(ctx, voice, path)


@bot.command()
async def playlist(ctx, *, command = None):
    # Цель команды - вывести текущий список песен
    author = ctx.author
    mention = ctx.author.mention

    # Возвращаем, если отправитель не подключен ни к какому из каналов
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    # Получаем канал пользователя
    server = ctx.guild
    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)

    # Выводим красивое отформатированное сообщение-список песен
    queue = sl.getWholeQueue(path)
    currentSongExists = sl.currentSongExists(path)
    await ctx.send(embed = ms.getSongListEmbed(mention, queue, currentSongExists))

@bot.command()
async def skip(ctx, *, command = None):
    # Пропускает текущую песню
    author = ctx.author
    mention = ctx.author.mention

    # Возвращаем, если отправитель не подключен ни к какому из каналов
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    # Получаем канал пользователя
    server = ctx.guild
    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)

    # Если что-то играет, пропускаем песню, если ничего не играет, выводим ошибку
    if voice.is_playing():
        currentsong = sl.getCurrentSong(path)
        voice.stop()
        await ctx.send(embed = ms.skipOneSongEmbed(currentsong))
    else:
        await ctx.send(embed = ms.nothingToSkipEmbed())

@bot.command()
async def clear(ctx, *, command = None):
    # Полностью очищает список песен и останавливает проигрывание
    author = ctx.author
    mention = ctx.author.mention

    # Возвращаем, если отправитель не подключен ни к какому из каналов
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    # Получаем канал пользователя
    server = ctx.guild
    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)

    # Очищаем список песен и прекращаем проигрывание, если что-то играет
    sl.cleanSongList(path)
    if voice.is_playing(): voice.stop()
    await ctx.send(embed = ms.weCleanSongListEmbed())

@bot.command()
async def pause(ctx, *, command = None):
    # Останавливает или возобновляет проигрывание
    author = ctx.author
    mention = ctx.author.mention

    # Возвращаем, если отправитель не подключен ни к какому из каналов
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    # Получаем канал пользователя
    server = ctx.guild
    channel_id = author.voice.channel.id

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен, возвращаем
        await ctx.send(embed = ms.weDontHaveVoiceChannelEmbed())
        return
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await ctx.send(embed = ms.youInTheOtherChannelEmbed())
        return

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)

    # Возвращаем, если нету строчки currentSong
    if not sl.currentSongExists(path):
        await ctx.send(embed = ms.haventCurrentSongEmbed())
        return

    # Если мы здесь, значит текущая песня точно есть и список не пуст
    # А значит если что-то играет - паузим, если ничего не играет - резумим (снимаем паузу)
    if voice.is_playing(): 
        voice.pause()
        await ctx.send(embed = ms.playlistOnPauseEmbed())
    else: 
        voice.resume()
        await ctx.send(embed = ms.playlistKillPauseEmbed())

@bot.command()
async def help(ctx, *, command = None):
    await ctx.send(embed = ms.helpCommandEmbed(ctx.guild))

@bot.command()
async def hundred(ctx, *, command = None):
    # Команда для работы со списком 100 лучших метал-альбомов
    author = ctx.author
    mention = ctx.author.mention
    server = ctx.guild

    # Для начала определяем с чем мы работаем
    # Либо с рандомным альбомом (/hundred), либо с конкретным (/hundred 1) (Paranoid)
    # По умолчанию - рандом
    rand = True

    # Если в параметры что-то ввели, то проверяем, если нет, то и так всё ок
    if command:
        params = command.split(" ")
        if len(params) > 1:
            # Параметров больше чем нужно
            await ctx.send(embed = ms.hundredErrorEmbed(mention))
            return
        
        if len(params) == 1:
            # Значит, выбрали конкретный альбом, мы обязаны проверить находится ли число от 1 до 100
            rand = False
            try:
                choice = int(params[0])
                if not (1 <= choice <= 100):
                    # Число вне диапазона, возвращаем
                    await ctx.send(embed = ms.hundredDigitErrorEmbed(mention))
                    return
            except:
                # Произошла какая-то ошибка при преобразовывании, возвращаем
                await ctx.send(embed = ms.hundredDigitErrorEmbed(mention))
                return

    # Если вызывающий команду не подключен ни к какому голосовому каналу, то возвращаем
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)
    song_name = sl.getSongName(path)

    try:
        ydl_options = {
                'format': 'bestaudio/best',
                'outtmpl': path + "notloaded" + os.sep + song_name,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }
                ],
            }

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            # При рандоме случайно генерируем ссылку
            # Если же выбран конкретный альбом, получаем ссылку именно на него
            if rand: url = sl.getHundredUrl()
            else: url = sl.getOneFromHundredUrl(choice)

            # Добавляем альбом в очередь песен
            info = ydl.extract_info(url, download = False)
            song_title = info.get('title', None)
            sl.addSong(path, song_name, song_title)

            # Скачиваем альбом в отдельном потоке
            t = Thread(target=download, args=[ydl, url, path, song_name])
            t.start()

            # Отправляем пользователю сообщение о добавлении альбома в очередь
            queue_len = len(sl.getQueue(path))
            if sl.currentSongExists(path): queue_len += 1
            await ctx.send(embed = ms.addToQueueEmbed(mention, song_title, queue_len))
    except Exception as e:
        # Произошла ошибка при скачивании, возвращаем функцию
        print("*[Dimebag] Произошла ошибка при скачивании альбома " + song_name)
        print(e)
        await ctx.send(embed = ms.downloadErrorEmbed(mention))
        return

    # Проигрывание альбома с учётом очереди
    await playSong(ctx, voice, path)

@bot.command()
async def likeit(ctx, *, command = None):
    # Команда для проигрывания случайного трека из 30 возможных (по моей выборке)
    author = ctx.author
    mention = ctx.author.mention
    server = ctx.guild

    # Если вызывающий команду не подключен ни к какому голосовому каналу, то возвращаем
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)
    song_name = sl.getSongName(path)

    try:
        ydl_options = {
                'format': 'bestaudio/best',
                'outtmpl': path + "notloaded" + os.sep + song_name,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }
                ],
            }

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            # Получаем случайную ссылку из 30
            url = sl.getLikeItUrl()

            # Добавляем песню в очередь песен
            info = ydl.extract_info(url, download = False)
            song_title = info.get('title', None)
            sl.addSong(path, song_name, song_title)

            # Скачиваем песню в отдельном потоке
            t = Thread(target=download, args=[ydl, url, path, song_name])
            t.start()

            # Отправляем пользователю сообщение о добавлении песни в очередь
            queue_len = len(sl.getQueue(path))
            if sl.currentSongExists(path): queue_len += 1
            await ctx.send(embed = ms.addToQueueEmbed(mention, song_title, queue_len))
    except Exception as e:
        # Произошла ошибка при скачивании, возвращаем функцию
        print("*[Dimebag] Произошла ошибка при скачивании альбома " + song_name)
        print(e)
        await ctx.send(embed = ms.downloadErrorEmbed(mention))
        return

    # Проигрывание песни с учётом очереди
    await playSong(ctx, voice, path)




# Блок команд связанных с love
@bot.command()
async def love(ctx, *, command = None):
    # Команда для работы со списком избранных композиций канала
    author = ctx.author
    mention = ctx.author.mention
    server = ctx.guild

    # Если вызывающий команду не подключен ни к какому голосовому каналу, то возвращаем
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми избранными песнями
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    pathfav = os.getcwd() + os.sep + "favourites" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)
    if not sl.checkFolder(pathfav): sl.createLoveList(pathfav)
    song_name = sl.getSongName(path)

    # Для начала определяем с чем мы работаем
    # Либо с рандомной песней (/love), либо с конкретной (/love 5)
    # По умолчанию - рандом
    rand = True
    loveList = sl.getLoveList(pathfav)

    # Если у нас вообще отсутствует loveList, то возвращаем
    if len(loveList) < 1:
        await ctx.send(embed = ms.youHaventLoveListEmbed(mention))
        return

    # Если в параметры что-то ввели, то проверяем, если нет, то и так всё ок
    if command:
        params = command.split(" ")
        if len(params) > 1:
            # Параметров больше чем нужно
            await ctx.send(embed = ms.noneArgsInLoveEmbed(mention))
            return
        
        if len(params) == 1:
            # Значит, выбрали конкретную песню, мы обязаны проверить находится ли число в правильном диапазоне
            rand = False
            try:
                choice = int(params[0])
                if not (1 <= choice <= len(loveList)):
                    # Число вне диапазона, возвращаем
                    await ctx.send(embed = ms.loveDigitErrorEmbed(mention, len(loveList)))
                    return
            except:
                # Произошла какая-то ошибка при преобразовывании, возвращаем
                await ctx.send(embed = ms.loveDigitErrorEmbed(mention, len(loveList)))
                return
            
    try:
        ydl_options = {
                'format': 'bestaudio/best',
                'outtmpl': path + "notloaded" + os.sep + song_name,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }
                ],
            }

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            # При рандоме случайно генерируем ссылку
            # Если же выбрана конкретная песня, получаем ссылку именно на неё
            if rand: url = sl.getLoveUrl(pathfav)
            else: url = sl.getOneFromLoveUrl(pathfav, choice)

            # Добавляем песню в очередь песен
            info = ydl.extract_info(url, download = False)
            song_title = info.get('title', None)
            sl.addSong(path, song_name, song_title)

            # Скачиваем песню в отдельном потоке
            t = Thread(target=download, args=[ydl, url, path, song_name])
            t.start()

            # Отправляем пользователю сообщение о добавлении песни в очередь
            queue_len = len(sl.getQueue(path))
            if sl.currentSongExists(path): queue_len += 1
            await ctx.send(embed = ms.addToQueueEmbed(mention, song_title, queue_len))
    except Exception as e:
        # Произошла ошибка при скачивании, возвращаем функцию
        print("*[Dimebag] Произошла ошибка при скачивании альбома " + song_name)
        print(e)
        await ctx.send(embed = ms.downloadErrorEmbed(mention))
        return

    # Проигрывание альбома с учётом очереди
    await playSong(ctx, voice, path)

@bot.command()
async def loveadd(ctx, *, command = None):
    # Добавляет ссылку в список избранных песен канала
    author = ctx.author
    mention = ctx.author.mention

    # Если не указали ссылку, то возвращаем
    if command == None:
        await ctx.send(embed = ms.noneArgsInLoveaddEmbed(mention))
        return
    
    # Если автор сообщения не подключен ни к какому голосовому, то возвращаем
    if author.voice == None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return
    
    # Если ссылка некорректна, возвращаем
    url = command.split(" ")[0]
    if not isUrlCorrect(url):
        await ctx.send(embed = ms.urlErrorEmbed(mention))
        return
    
    # Создаём файл love, если его ещё нет
    channel_id = author.voice.channel.id
    path = os.getcwd() + os.sep + "favourites" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createLoveList(path)

    # Добавляем правильный url в существующую папку
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download = False)
            title = info.get('title', None)
        
        sl.addUrlToLove(path, url, title)
        await ctx.send(embed = ms.successAddToLoveEmbed(mention, title))
    except:
        # Что-то пошло не по плану
        print("*[Dimebag] Произошла ошибка при добавлении песни в любимые")
        print(e)
        await ctx.send(embed = ms.addToLoveErrorEmbed(mention))
        return
    
@bot.command()
async def lovelist(ctx, *, command = None):
    # Цель команды - вывести избранный список песен
    author = ctx.author
    mention = ctx.author.mention

    # Возвращаем, если отправитель не подключен ни к какому из каналов
    if author.voice is None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return

    # Получаем канал пользователя
    server = ctx.guild
    channel_id = author.voice.channel.id
    voice_channel = discord.utils.get(server.voice_channels, id = channel_id)

    # Подключаем бота к каналу, если он ещё не подключен
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice is None:
        # На случай, если бот ни в какой из каналов не подключен
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)
    elif voice.channel.id != channel_id:
        # На случай, если пользователь и бот находятся в разных каналах
        await voice.disconnect()
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=server)

    # При вводе команды каждому голосовому каналу создаётся отдельная папка со всеми песнями из очереди
    # Создаём папку для канала, если её ещё нет
    path = os.getcwd() + os.sep + "cash" + os.sep + str(channel_id) + os.sep
    pathfav = os.getcwd() + os.sep + "favourites" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createFolder(path)
    if not sl.checkFolder(pathfav): sl.createLoveList(pathfav)

    # Выводим красивое отформатированное сообщение-список песен
    lovelist = sl.getLoveList(pathfav)
    await ctx.send(embed = ms.getLoveListEmbed(lovelist))

@bot.command()
async def loveremove(ctx, *, command = None):
    # Удаляет ссылку из списка избранных песен канала
    author = ctx.author
    mention = ctx.author.mention

    # Если не указали номер , то возвращаем
    if command == None:
        await ctx.send(embed = ms.noneArgsInLoveRemoveEmbed(mention))
        return
    
    # Если автор сообщения не подключен ни к какому голосовому, то возвращаем
    if author.voice == None:
        await ctx.send(embed = ms.voiceErrorEmbed(mention))
        return
    
    # Создаём файл love, если его ещё нет
    channel_id = author.voice.channel.id
    path = os.getcwd() + os.sep + "favourites" + os.sep + str(channel_id) + os.sep
    if not sl.checkFolder(path): sl.createLoveList(path)
    
    loveList = sl.getLoveList(path)

    # Если у нас вообще отсутствует loveList, то возвращаем
    if len(loveList) < 1:
        await ctx.send(embed = ms.youHaventLoveListEmbed(mention))
        return

    # Если в параметры что-то ввели, то проверяем, если нет, то и так всё ок
    if command:
        params = command.split(" ")
        if len(params) > 1:
            # Параметров больше чем нужно
            await ctx.send(embed = ms.noneArgsInLoveRemoveEmbed(mention))
            return
        
        if len(params) == 1:
            # Значит, выбрали конкретную песню, мы обязаны проверить находится ли число в правильном диапазоне
            try:
                choice = int(params[0])
                if not (1 <= choice <= len(loveList)):
                    # Число вне диапазона, возвращаем
                    await ctx.send(embed = ms.loveRemoveDigitErrorEmbed(mention, len(loveList)))
                    return
            except:
                # Произошла какая-то ошибка при преобразовывании, возвращаем
                await ctx.send(embed = ms.loveRemoveDigitErrorEmbed(mention, len(loveList)))
                return

    # Удаляем песню из списка
    killedSong = sl.killOneLoveSong(path, choice)
    await ctx.send(embed = ms.weRemoveOneLoveSongEmbed(mention, killedSong.split("[]")[0]))

bot.run(token)