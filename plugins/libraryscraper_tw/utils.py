from translate import Translator
from googletrans import Translator


def translat_en_zh_text(text,from_lang = "en", zhconv = None):
    text_zh_cn = Translator(from_lang=from_lang, to_lang="ZH").translate(text)
    return zhconv.convert(text_zh_cn, "zh-tw")

def translat_en_zh_tw_text(text):
    translator = Translator()
    return translator.translate(text, src='en', dest='zh-tw').text



# if __name__ == "__main__":
#     text_to_translate = "Ciro Di Marzio, right hand man of clan boss Pietro Savastano, and Ciro's fatherly friend Attilio set fire to Salvatore Conte's home to cut Salvatore down to size – him, the ruthless upcoming contender on the Savastano clan's turf."
#     print(translat_en_zh_tw_text(text_to_translate))


