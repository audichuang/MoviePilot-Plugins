from pathlib import Path
from typing import List, Any, Union

from app import schemas
from app.chain.media import MediaChain
from app.core.config import settings
from app.core.metainfo import MetaInfo, MetaInfoPath
from app.schemas import MediaType

from app.plugins.mediascraper.scrape_transfer import Get_TW_info

from app.plugins.mediascraper.scraper import TmdbScraper
from app.plugins.mediascraper.scrape_metadata import scrape_metadata


def scrape(src_path, scrape_path: str, tmdbscraper: TmdbScraper) -> Any:
    """
    刮削媒体信息
    """
    if not scrape_path:
        return schemas.Response(success=False, message="刮削路径无效")
    scrape_path = Path(scrape_path)
    if not scrape_path.exists():
        return schemas.Response(success=False, message="刮削路径不存在")
    # 识别
    chain = MediaChain()
    meta = MetaInfoPath(src_path)
    mediainfo = chain.recognize_media(meta)
    if not mediainfo:
        return schemas.Response(success=False, message="刮削失败，无法识别媒体信息")
    mediainfo_tw = Get_TW_info.get_media_info(mediainfo)

    # 刮削
    scrape_metadata(
        scraper=tmdbscraper,
        path=scrape_path,
        mediainfo=mediainfo_tw,
        transfer_type=settings.TRANSFER_TYPE,
        force_img=False,
        force_nfo=True,
    )
    return schemas.Response(success=True, message="刮削完成")


if __name__ == "__main__":
    from app.modules.themoviedb.tmdbapi import TmdbApi
    from app.plugins.mediascraper.scraper import TmdbScraper

    scrape(
        path="/home/audichuang/media_6/test/日韩剧/玫瑰的故事 (2024)",
        tmdbscraper=TmdbScraper(TmdbApi()),
    )
