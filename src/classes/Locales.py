from typing import Any
import json


class Locale:

    supported_locales = [
        'en', 'es', 'id', 'fr', 'de', 'jp', 'kr', 'cn', 'tw', 'ru', 'ar', 'pt', 'it', 'nl', 'tr', 'fl'
    ]

    def __init__(self, locale_file: str | dict[str, str]):
        self.default_locale: str = 'en'
        self.current_lang: str = 'en'
        self.data_locale: dict[str, Any] = {}
        if isinstance(locale_file, dict):
            if self.default_locale not in locale_file:
                self.default_locale = list(locale_file.keys())[0]
                self.current_lang = self.default_locale
            for key, value in locale_file.items():
                with open(value, 'r') as f:
                    self.data_locale[key] = json.load(f)
        else:
            with open(locale_file, 'r') as f:
                self.data_locale[self.default_locale] = json.load(f)

    def __get_value(self, key: str, default):
        keys = key.split('.')
        value = self.data_locale[self.current_lang]
        for k in keys:
            value = value.get(k, default)
        return value

    def set_locale(self, lang: str):
        if lang in self.supported_locales:
            self.current_lang = lang
        else:
            self.current_lang = self.default_locale

    def t(self, key: str, **kwargs):
        translation = self.__get_value(key, {})
        if isinstance(translation, str):
            return translation.replace("%{", "{").format(**kwargs)
        return translation

    def conjunction_list(self, items) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]

        match self.current_lang:
            case 'en':
                return ", ".join(items[:-1]) + " and " + items[-1]
            case 'es':
                return ", ".join(items[:-1]) + " y " + items[-1]
            case 'id':
                return ", ".join(items[:-1]) + " dan " + items[-1]
            case 'fr':
                return ", ".join(items[:-1]) + " et " + items[-1]
            case 'de':
                return ", ".join(items[:-1]) + " und " + items[-1]
            case 'jp':
                return ", ".join(items[:-1]) + " と " + items[-1]
            case 'kr':
                return ", ".join(items[:-1]) + " 그리고 " + items[-1]
            case 'cn':
                return ", ".join(items[:-1]) + " 和 " + items[-1]
            case 'tw':
                return ", ".join(items[:-1]) + " 和 " + items[-1]
            case 'ru':
                return ", ".join(items[:-1]) + " и " + items[-1]
            case 'ar':
                return ", ".join(items[:-1]) + " و " + items[-1]
            case 'pt':
                return ", ".join(items[:-1]) + " e " + items[-1]
            case 'it':
                return ", ".join(items[:-1]) + " e " + items[-1]
            case 'nl':
                return ", ".join(items[:-1]) + " en " + items[-1]
            case 'tr':
                return ", ".join(items[:-1]) + " ve " + items[-1]
            case 'fl':
                return ", ".join(items[:-1]) + " og " + items[-1]
            case _:
                return ", ".join(items[:-1]) + " and " + items[-1]
