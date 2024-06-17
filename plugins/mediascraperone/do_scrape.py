from pathlib import Path
from typing import List, Any, Union

from app import schemas
from app.chain.media import MediaChain
from app.core.config import settings
from app.core.metainfo import MetaInfo, MetaInfoPath
from app.schemas import MediaType

from app.plugins.mediascraperone.scrape_transfer import Get_TW_info
from app.plugins.mediascraperone.scraper import TmdbScraper
from app.plugins.mediascraperone.scrape_metadata import scrape_metadata


def scrape(path: str, tmdbscraper: TmdbScraper, type=None, tmdbid=None) -> Any:
    """
    刮削媒体信息
    """
    if not path:
        return schemas.Response(success=False, message="刮削路径无效")
    scrape_path = Path(path)
    if not scrape_path.exists():
        return schemas.Response(success=False, message="刮削路径不存在")
    # 识别
    chain = MediaChain()
    meta = MetaInfoPath(scrape_path)
    mediainfo = chain.recognize_media(meta)
    if not mediainfo:
        return schemas.Response(success=False, message="刮削失败，无法识别媒体信息")
    mediainfo_tw = Get_TW_info.get_media_info(mediainfo)
    # 刮削
    scrape_metadata(scraper =tmdbscraper, path=scrape_path, mediainfo=mediainfo_tw, transfer_type=settings.TRANSFER_TYPE, force_img=False, force_nfo=True)
    return schemas.Response(success=True, message="刮削完成")


if __name__ == "__main__":
    from app.modules.themoviedb.tmdbapi import TmdbApi
    from app.plugins.mediascraper.scraper import TmdbScraper

    # scrape(
    #     path="/home/audichuang/media_3/电视剧/国产剧/三生三世十里桃花 (2017)",
    #     tmdbscraper=TmdbScraper(TmdbApi()),
    # )
    # 列出該路徑全部資料夾

    folders = ["media", "media_2", "media_3", "media_4", "media_5", "media_6"]
    for folder in folders:
        for p in Path(f"/home/audichuang/{folder}/电视剧/欧美剧").iterdir():
            scrape(path=p, tmdbscraper=TmdbScraper(TmdbApi()))
