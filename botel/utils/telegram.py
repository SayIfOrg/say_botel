from telebot.types import Message


def get_start_param(message: Message):
    actual_value = message.text.split(" ")[1]
    return actual_value
