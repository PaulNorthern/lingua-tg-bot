import os
import telebot
from googletrans import Translator
import openai
from telebot import types
import random
from random import shuffle
from dotenv import load_dotenv

load_dotenv()

# подключаем токены
bot = telebot.TeleBot(os.getenv('TG_TOKEN'))
openai.api_key = os.getenv('OPEN_AI_TOKEN')

translator = Translator(service_urls=['translate.googleapis.com'])


# возвращаем варианты ответов от нейросети
def make_test(word):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="I'm composing a word test. I give you the word. You give me 3 options of wrong answers."
               " No repeating answers."
               "\nExample:\nI: Frog\nYou: \nElephant\nDog\nCat\nI:" + word + " \nYou:\n",
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=1
    )
    return response['choices'][0]['text']


def read_lines(filename):
    with open(filename, "r") as file:
        lines = file.readlines()
        return lines

def get_top10(lines):
    top10 = lines[-10:]
    return top10

def get_random_word(top10):
    word = random.choice(top10)[:-1] if len(top10) > 0 else 'Raccoon'
    return word

def random_word(filename):
    try:
        lines = read_lines(filename)
        top10 = get_top10(lines)
        word = get_random_word(top10)
        return word
    except FileNotFoundError:
        print("Файл не найден. Создаю новый файл...")
        with open(filename, "w+") as file:
            print("Файл успешно создан и открыт для чтения.")
            lines = read_lines(filename)
            top10 = get_top10(lines)
            word = get_random_word(top10)
            file.write(word + "\n")
            return word


# обрабатываем команду /start
@bot.message_handler(commands=['start'])
def show_start(message):
    bot.send_photo(message.chat.id,
                   photo=open("Raccoon1.png", 'rb'),
                   caption="")

    bot.send_message(message.chat.id,
                     text="<u>Привет! Я бот, который помогает изучать новые "
                          "английские слова и лучше их запомнить.</u>\n\n"
                          "Напишите английское слово и отправьте его мне",
                     parse_mode="html")
    bot.send_message(message.chat.id,
                     text="👇")


# обрабатываем команду /help
@bot.message_handler(commands=['help'])
def show_start(message):
    bot.send_photo(message.chat.id,
                   photo=open("Raccoon2.png", 'rb'),
                   caption="")
    bot.send_message(message.chat.id,
                     text="<b>Как пользоваться ботом</b>\n\n"
                          "💡 Когда вы читаете книгу на "
                          "английском языке и встречаете <b>новое слово</b>, отправьте его мне, "
                          "я его переведу и запишу в словарик.\n\n"
                          "💡 Вы можете <b>посмотреть последние добавленные слова</b> с помощью команды "
                          "/vocabulary \n\n"
                          "💡 С помощью команды /compose вы можете"
                          " сгенерировать <b>примеры использования</b> новых слов \n\n"
                          "💡 Вы также можете получить <b>индивидуальный тест</b> для лучшего запоминания "
                          "последних добавленных слов. Для этого выберите команду /test\n\n"
                          "Если вы хотите снова меня увидеть, напишите /start\n\n",
                     parse_mode="html")

# обрабатываем команду /compose
@bot.message_handler(commands=['compose'])
def show_start(message):
    with open("vocabulary.txt", "r") as file:
        words = file.readlines()
    n = len(words)
    word1 = words[n - 1]
    word2 = words[n - 2]
    word3 = words[n - 3]
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Compose a sentence using "
               "words" + word1 + ", " + word2 + ", " + word3 +
               "return each of these words in <b></b> tag",
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=1
    )
    bot.send_message(message.chat.id,
                     text=response['choices'][0]['text'], parse_mode="html")


# обрабатываем команду /test
@bot.message_handler(commands=['test'])
def show_test(message):
    # вызываем функцию random_word
    word = random_word("vocabulary.txt")
    word = translator.translate(word, src="ru", dest="en").text
    # генерируем тест и разбиваем ответ от нейросети на отдельные строки
    test = make_test(word.title()).split("\n")
    # добавляем в список наше искомое
    test.append(word.title())
    # добавляем в файл верный ответ, переведенный на русский
    with open("current_answer.txt", "w") as file:
        file.write(translator.translate(word, src="ru", dest="en").text.title())
    # перемешиваем ответы
    shuffle(test)

    # for i in range(0, 4):
    #     test[i] = translator.translate(test[i], src="en", dest="ru").text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    btnList = [
        types.KeyboardButton(test[0].title()),
        types.KeyboardButton(test[1].title()),
        types.KeyboardButton(test[2].title()),
        types.KeyboardButton(test[3].title()),
    ]

    # создаем кнопки с вариантами ответов и добавляем в разметку
    markup.add(*btnList)
    bot.send_message(message.chat.id,
                     text="Как перевести слово <b>" + word.title() + "</b>?\nВыберите правильный ответ:",
                     parse_mode="html", reply_markup=markup)


# обрабатываем команду /vocabulary
@bot.message_handler(commands=['vocabulary'])
def show_vocabulary(message):
    with open("vocabulary.txt", "r") as file:
        lines = file.readlines()[-10:]
    for line in reversed(lines):
        bot.send_message(message.chat.id, text=line)


# обрабатываем текстовое сообщение от пользователя
@bot.message_handler(content_types=['text'])
def handle_message(message):
    try:
        with open("current_answer.txt", "r") as file:
            word = file.readlines()
    except FileNotFoundError:
        c_file = open("current_answer.txt", "w")
        c_file.close()
        with open("current_answer.txt", "r") as file:
            word = file.readlines()

    hidemarkup = types.ReplyKeyboardRemove()

    if not word:
        if message.text.find(" ") > 0:
            bot.send_message(message.chat.id, text="Простите, мы на данный момент принимаем только отдельные слова")
        else:
            bot.send_message(message.chat.id, text=translator.translate(message.text, src="ru", dest="en").text,
                             reply_markup=hidemarkup)
            with open("vocabulary.txt", "a") as v_file:
                v_file.write(message.text.title() + "\n")
    elif word[0] == message.text:
        bot.send_message(message.chat.id, text=random.choice("🥳🎉👯🎊👍🦝🤩🥂🎂🕺"))
        bot.send_message(message.chat.id, text="Это верный ответ!")
        bot.send_message(message.chat.id, text="Вы можете продолжить проходить /test, либо переведите новое слово ",
                         reply_markup=hidemarkup)
    else:
        bot.send_message(message.chat.id, text="😕")
        bot.send_message(message.chat.id, text="Увы, это не " + message.text + ", а " + word[0])
        bot.send_message(message.chat.id, text="Вы можете пройти еще один /test или переведите новое слово",
                         reply_markup=hidemarkup)
    with open("current_answer.txt", "w") as file:
        file.write("")


bot.polling()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
