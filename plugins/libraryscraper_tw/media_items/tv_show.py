from app.plugins.libraryscraper_tw.tmdb_details import (
    _get_tv_details,
    _get_tv_season_details,
    _get_tv_episode_details,
)
from app.plugins.libraryscraper_tw.utils import translat_en_zh_text
from app.log import logger

import zhconv

# from plugins.libraryscraper_tw.tmdb_details import (
#     _get_tv_details,
#     _get_tv_season_details,
#     _get_tv_episode_details,
# )
# from plugins.libraryscraper_tw.utils import translat_en_zh_text



class TvShow:
    def get_tvshow_nfo_update_dict(tmdb_id: int, zhconv):
        """
        根据 TMDB ID 获取电视剧的 NFO 更新字典。

        Args:
            tmdb_id (int): TMDB 电视剧 ID。

        Returns:
            Dict[str, str]: 包含标题、剧情、概要和原始标题的字典。
        """
        details = _get_tv_details(tmdb_id)
        translate = 0
        if details["overview"] == "":
            translate = 1
            details = _get_tv_details(tmdb_id, language="zh-CN")
            if details["overview"] == "":
                translate = 2
                details = _get_tv_details(tmdb_id, language="en-US")

        if translate == 0:
            logger.info(f"電視劇 {details['name']} 取得繁體中文資訊")
            overview = details["overview"]
            title = details["name"]
        elif translate == 1:
            logger.info(f"電視劇 {details['name']} 取得簡體中文資訊，將翻譯成繁體中文")
            overview = zhconv.convert(details["overview"], "zh-tw")
            title = zhconv.convert(details["name"], "zh-tw")
        elif translate == 2:
            logger.info(f"電視劇 {details['name']} 取得英文資訊，將翻譯成繁體中文")
            overview = translat_en_zh_text(details["overview"], zhconv=zhconv)
            title = translat_en_zh_text(details["name"], zhconv=zhconv)

        if overview is None:
            overview = ""

        original_title = _get_tv_details(tmdb_id, language="en-US")["name"]

        return {
            "title": title,
            "plot": overview,
            "outline": overview,
            "originaltitle": original_title,
        }

    def get_season_nfo_update_dict(tmdb_id: int, season_number: int, zhconv):
        """
        根据 TMDB ID 和季数获取季的 NFO 更新字典。

        Args:
            tmdb_id (int): TMDB 电视剧 ID。
            season_number (int): 季数。

        Returns:
            Dict[str, str]: 包含标题、剧情和概要的字典。
        """

        details = _get_tv_season_details(tmdb_id, season_number)
        translate = 0
        if details["overview"] == "":
            translate = 1
            details = _get_tv_season_details(tmdb_id, season_number, language="zh-CN")
            if details["overview"] == "":
                translate = 2
                details = _get_tv_season_details(
                    tmdb_id, season_number, language="en-US"
                )

        if translate == 0:
            logger.info(f"電視劇 {details['name']} 第 {season_number} 季取得繁體中文資訊")
            overview = details["overview"]
            title = details["name"]
        elif translate == 1:
            logger.info(
                f"電視劇 {details['name']} 第 {season_number} 季取得簡體中文資訊，將翻譯成繁體中文"
            )
            overview = zhconv.convert(details["overview"], "zh-tw")
            title = zhconv.convert(details["name"], "zh-tw")
        elif translate == 2:
            logger.info(
                f"電視劇 {details['name']} 第 {season_number} 季取得英文資訊，將翻譯成繁體中文"
            )
            overview = translat_en_zh_text(details["overview"], zhconv=zhconv)
            title = translat_en_zh_text(details["name"], zhconv=zhconv)

        if overview is None:
            overview = ""
        return {
            "title": title,
            "plot": overview,
            "outline": overview,
        }

    def get_episode_nfo_update_dict(
        tmdb_id: int, season_number: int, episode_number: int, zhconv
    ):
        """
        根据 TMDB ID、季数和集数获取集的 NFO 更新字典。

        Args:
            tmdb_id (int): TMDB 电视剧 ID。
            season_number (int): 季数。
            episode_number (int): 集数。

        Returns:
            Dict[str, str]: 包含标题、剧情和概要的字典。
        """
        details = _get_tv_episode_details(tmdb_id, season_number, episode_number)
        translate = 0
        if details["overview"] == "":
            translate = 1
            details = _get_tv_episode_details(
                tmdb_id, season_number, episode_number, language="zh-CN"
            )
            if details["overview"] == "":
                translate = 2
                details = _get_tv_episode_details(
                    tmdb_id, season_number, episode_number, language="en-US"
                )

        if translate == 0:
            logger.info(
                f"電視劇 {details['name']} 第 {season_number} 季第 {episode_number} 集取得繁體中文資訊"
            )
            overview = details["overview"]
            title = details["name"]
        elif translate == 1:
            logger.info(
                f"電視劇 {details['name']} 第 {season_number} 季第 {episode_number} 集取得簡體中文資訊，將翻譯成繁體中文"
            )
            overview = zhconv.convert(details["overview"], "zh-tw")
            title = zhconv.convert(details["name"], "zh-tw")
        elif translate == 2:
            logger.info(
                f"電視劇 {details['name']} 第 {season_number} 季第 {episode_number} 集取得英文資訊，將翻譯成繁體中文"
            )
            overview = translat_en_zh_text(details["overview"], zhconv=zhconv)
            title = translat_en_zh_text(details["name"], zhconv=zhconv)

        if overview is None:
            overview = ""
        return {
            "title": title,
            "plot": overview,
            "outline": overview,
        }


# if __name__ == "__main__":
#     tmdb_id = 2734
#     season_number = 1
#     episode_number = 2
#     print(TvShow.get_tvshow_nfo_update_dict(tmdb_id, zhconv))
#     print(TvShow.get_season_nfo_update_dict(tmdb_id, season_number, zhconv))
#     print(
#         TvShow.get_episode_nfo_update_dict(
#             tmdb_id, season_number, episode_number, zhconv
#         )
#     )
