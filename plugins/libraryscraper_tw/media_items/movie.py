from app.plugins.libraryscraper_tw.tmdb_details import _get_movie_details
from app.plugins.libraryscraper_tw.utils import translat_en_zh_text, translat_en_zh_tw_text
from app.log import logger
# from plugins.libraryscraper_tw.tmdb_details import _get_movie_details
# from plugins.libraryscraper_tw.utils import translat_en_zh_text
import zhconv


class Movie:
    def get_movie_nfo_update_dict(tmdb_id: int, zhconv=None):
        """
        根据 TMDB ID 获取电影的 NFO 更新字典。

        Args:
            tmdb_id (int): TMDB 电影 ID。

        Returns:
            Dict[str, str]: 包含标题、剧情、概要和原始标题的字典。
        """
        details = _get_movie_details(tmdb_id)
        translate = 0
        if details["overview"] == "":
            translate = 1
            details = _get_movie_details(tmdb_id, language="zh-CN")
            if details["overview"] == "":
                translate = 2
                details = _get_movie_details(tmdb_id, language="en-US")

        if translate == 0:
            logger.info(f"電影 {details['title']} 取得繁體中文資訊")
            # print(f"電影 {details['title']} 取得繁體中文資訊")
            overview = details["overview"]
            title = details["title"]
        elif translate == 1:
            logger.info(f"電影 {details['title']} 取得簡體中文資訊，將翻譯成繁體中文")
            # print(f"電影 {details['title']} 取得簡體中文資訊，將翻譯成繁體中文")
            overview = zhconv.convert(details["overview"], "zh-tw")
            title = zhconv.convert(details["title"], "zh-tw")
        elif translate == 2:
            logger.info(f"電影 {details['title']} 取得英文資訊，將翻譯成繁體中文")
            # print(f"電影 {details['title']} 取得英文資訊，將翻譯成繁體中文")
            # overview = translat_en_zh_text(details["overview"], zhconv=zhconv)
            # title = translat_en_zh_text(details["title"], zhconv=zhconv)
            overview = translat_en_zh_tw_text(details["overview"])
            title = translat_en_zh_tw_text(details["name"])

        if overview is None:
            overview = ""
        overview = overview.strip().replace("\r", "").replace("\n", "")
        logger.error(f"得到電影 {title} 繁體中文概要: {overview}")
        original_title = _get_movie_details(tmdb_id, language="en-US")["title"]

        return {
            "title": title,
            "plot": overview,
            "outline": overview,
            "originaltitle": original_title,
        }


if __name__ == "__main__":
    print(Movie.get_movie_nfo_update_dict(850888, zhconv))
