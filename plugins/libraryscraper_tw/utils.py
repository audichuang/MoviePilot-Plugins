from translate import Translator


def translat_en_zh_text(text,from_lang = "en", zhconv = None):
    text_zh_cn = Translator(from_lang=from_lang, to_lang="ZH").translate(text)
    return zhconv.convert(text_zh_cn, "zh-tw")


# if __name__ == "__main__":
#     text = "Ko Gun's school life lacks any significant interests as his busy part-time schedules consume his time after classes. However, everything changes when Se Young, a transfer student from LA, joins his class and ends up sitting next to him. Initially indifferent, their frequent encounters gradually ignite a spark in Gun's life."
#     from_lang = "en"
#     import zhconv

#     text = translat_en_zh_text(text, from_lang, zhconv)
#     print(text)
