from pathlib import Path

from app.core.config import settings
from app.core.context import MediaInfo
from app.core.meta import MetaBase
from app.log import logger
from app.modules.themoviedb.scraper import TmdbScraper

from app.utils.system import SystemUtils


def scrape_metadata(scraper: TmdbScraper, path: Path, mediainfo: MediaInfo, transfer_type: str,
                        metainfo: MetaBase = None, force_nfo: bool = False, force_img: bool = False) -> None:
    """
    刮削元数据
    :param path: 媒体文件路径
    :param mediainfo:  识别的媒体信息
    :param metainfo: 源文件的识别元数据
    :param transfer_type:  转移类型
    :param force_nfo:  强制刮削nfo
    :param force_img:  强制刮削图片
    :return: 成功或失败
    """
    if settings.SCRAP_SOURCE != "themoviedb":
        return None

    if SystemUtils.is_bluray_dir(path):
        # 蓝光原盘
        logger.info(f"开始刮削蓝光原盘：{path} ...")
        scrape_path = path / path.name
        scraper.gen_scraper_files(mediainfo=mediainfo,
                                        file_path=scrape_path,
                                        transfer_type=transfer_type,
                                        metainfo=metainfo,
                                        force_nfo=force_nfo,
                                        force_img=force_img)
    elif path.is_file():
        # 单个文件
        logger.info(f"开始刮削媒体库文件：{path} ...")
        scraper.gen_scraper_files(mediainfo=mediainfo,
                                        file_path=path,
                                        transfer_type=transfer_type,
                                        metainfo=metainfo,
                                        force_nfo=force_nfo,
                                        force_img=force_img)
    else:
        # 目录下的所有文件
        logger.info(f"开始刮削目录：{path} ...")
        for file in SystemUtils.list_files(path, settings.RMT_MEDIAEXT):
            if not file:
                continue
            scraper.gen_scraper_files(mediainfo=mediainfo,
                                            file_path=file,
                                            transfer_type=transfer_type,
                                            force_nfo=force_nfo,
                                            force_img=force_img)
    logger.info(f"{path} 刮削完成")