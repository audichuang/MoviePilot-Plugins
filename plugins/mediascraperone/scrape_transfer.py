from app.plugins.mediascraperone.get_tmdb_detail_by_language import (
    _get_tv_season_details,
    _get_tv_details,
    _get_movie_details,
)
from app.utils.string import StringUtils
from app.schemas import MediaType
import zhconv
import re


class Get_TW_info:
    @staticmethod
    def convert_CN_to_TW(text: str) -> str:
        """
        簡體中文轉繁體中文
        """
        return zhconv.convert(text, "zh-tw")

    @staticmethod
    def get_media_info(cn_media_info):
        if cn_media_info.type == MediaType.TV:
            tw_media_info = _get_tv_details(cn_media_info.tmdb_id, language="zh-TW")
            en_media_info = _get_tv_details(cn_media_info.tmdb_id, language="en-US")
        elif cn_media_info.type == MediaType.MOVIE:
            tw_media_info = _get_movie_details(cn_media_info.tmdb_id, language="zh-TW")
            en_media_info = _get_movie_details(cn_media_info.tmdb_id, language="en-US")

        # title
        # 從tmdb_api獲取 tv是name, movie是title
        if cn_media_info.type == MediaType.TV:
            if tw_media_info["name"] != "":
                cn_media_info.title = Get_TW_info.convert_CN_to_TW(
                    tw_media_info["name"]
                )
            else:
                cn_media_info.title = Get_TW_info.convert_CN_to_TW(cn_media_info.title)
            if en_media_info["name"] != "":
                cn_media_info.original_title = en_media_info["name"]
        elif cn_media_info.type == MediaType.MOVIE:
            if tw_media_info["title"] != "":
                cn_media_info.title = Get_TW_info.convert_CN_to_TW(
                    tw_media_info["title"]
                )
            else:
                cn_media_info.title = Get_TW_info.convert_CN_to_TW(cn_media_info.title)
            if en_media_info["title"] != "":
                cn_media_info.original_title = en_media_info["title"]

        # overview
        if tw_media_info["overview"] != "":
            cn_media_info.overview = Get_TW_info.convert_CN_to_TW(
                tw_media_info["overview"]
            )
        else:
            cn_media_info.overview = Get_TW_info.convert_CN_to_TW(
                cn_media_info.overview
            )

        return cn_media_info

    @staticmethod
    def is_episode_format(text):
        # 定義正則表達式來匹配 "第 X 集" 的格式
        pattern = r"^第\s*\d+\s*集$"
        return re.match(pattern, text) is not None

    @staticmethod
    def get_tv_season_detail(tmdbid: int, season_number: int, cn_info):
        tw_info = _get_tv_season_details(tmdbid, season_number, language="zh-TW")
        # cn_info = _get_tv_season_details(tmdbid, season_number, language='zh-CN')
        for i in range(len(tw_info["episodes"])):
            if Get_TW_info.is_episode_format(tw_info["episodes"][i]["name"]):
                if not Get_TW_info.is_episode_format(cn_info["episodes"][i]["name"]):
                    tw_info["episodes"][i]["name"] = Get_TW_info.convert_CN_to_TW(
                        cn_info["episodes"][i]["name"]
                    )
            if tw_info["episodes"][i]["overview"] == "":
                if cn_info["episodes"][i]["overview"] != "":
                    tw_info["episodes"][i]["overview"] = Get_TW_info.convert_CN_to_TW(
                        cn_info["episodes"][i]["overview"]
                    )
        return tw_info


if __name__ == "__main__":
    tmdbid = 229202
    detail = Get_TW_info.get_tv_season_detail(tmdbid, 1)
    print(detail)
