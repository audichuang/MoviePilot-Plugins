SIZE_MISTAKE_RANGE = 0.055  # % of the size

CATRGORY_CHINESE = ["华语电影", "国产剧"]


SUBSTITUTE_KEYWORD_LIST = [
    "双语",
    "中英",
    "简繁",
    "官译",
    "简英",
    "繁英",
    "繁,英",
    "英,繁",
]

SITE_SCORES = {
    "朋友": 100,
    "彩虹岛": 150,
    "观众": 1000,
    "听听歌": 300,
    "馒头": 300,
    "我堡": 100,
    "憨憨": 100,
    "UBits": 50,
    "52pt": 5,
    "麒麟": 5,
    "AGSVPT": 5,
    "织梦": 5,
    "PT时间": 3,
    "咖啡": 3,
    "花梨月下": 3,
    "象站": 3,
    "红叶PT": 3,
    "明教": 3,
    "冰淇淋": 3,
    "1PTBA": 3,
    "AGSVPT": 3,
    "蟹黄堡": 3,
    "红豆饭": 50,
    "学校": 100,
    "青蛙": 3,
    "DEFAULT": 1,
}
RESOURCE_TEAM_SCORES = {
    "adweb": 10,
    "qhstudio": 4,
    "hhanclub": 4,
    "chdweb": 3,
    "frds": 2,
    "default": 1,
}

DOWNLOAD_SITE_BONUS = {
    "馒头": 1,
    "憨憨": 0.05,
    "学校": 3,
    "织梦": 0.6,
    "观众": 0.9,
    "我堡": 0.7,
    "象站": 3,
    "红叶PT": 3,
    "明教": 3,
    "听听歌": 3,
    "1PTBA": 3,
    "蟹黄堡": 3,
    "红豆饭": 3,
    "彩虹岛": 0.9,
    "UBits": 1.8,
    "麒麟": 0.4,
    "52pt": 2.2,
    "冰淇淋": 0.1,
    "咖啡": 0.7,
    "AGSVPT": 0.4,
    "花梨月下": 3,
    "PT时间": 0.2,
    "青蛙": 3,
    "朋友": 5,
    "DEFAULT": 1,
}
SIZE_COEFFICIENT_LIST = [
    (500000, 10),
    (300000, 6),
    (200000, 5),
    (100000, 4),
    (80000, 3),
    (50000, 2),
    (20000, 1.5)
]

DOWNLOAD_VOLUME_BONUS = {
    "2X免费": 0.1,
    "2X 50%": 0.4,
    "2X": 0.6,
    "免费": 0.2,
    "50%": 0.8,
    "30%": 1.1,
    "普通": 1.8,
}

DEFAULT_FOLDER_NUMBER = "4"
FOLDER_DICT = {"1": "media", "2": "media2", "3": "media3", "4": "media4"}


def get_dir_path_and_type(folder_name, media_type):
    if media_type == "电影":
        return {"path": f"/{folder_name}/源文件/电影", "type": "movie"}
    elif media_type == "电视剧":
        return {"path": f"/{folder_name}/源文件/电视剧", "type": "tv"}
    elif media_type == "动漫":
        return {"path": f"/{folder_name}/源文件/动漫", "type": "tv"}
    else:
        raise ValueError("Invalid media type")
