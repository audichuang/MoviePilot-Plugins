import time
from typing import Any, List, Dict, Tuple

from app.core.config import settings
from app.core.context import MediaInfo
from app.modules.themoviedb.tmdbapi import TmdbApi
from app.plugins.mediascraperone.scraper import TmdbScraper

from app.core.event import eventmanager, Event
# from app.modules.emby import Emby
# from app.modules.jellyfin import Jellyfin
# from app.modules.plex import Plex
from app.plugins import _PluginBase
from app.schemas import TransferInfo, RefreshMediaItem
from app.schemas.types import EventType
from app.log import logger
from app.db.transferhistory_oper import TransferHistoryOper
from app.plugins.mediascraperone.do_scrape import scrape
from app.utils.system import SystemUtils
from app.core.config import settings
from pathlib import Path


class MediaScraperOne(_PluginBase):
    # 插件名称
    plugin_name = "一次性刮"
    # 插件描述
    plugin_desc = "一次性刮削繁體中文資訊。"
    # 插件图标
    plugin_icon = "scraper.png"
    # 插件版本
    plugin_version = "0.5"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "media_scraper_one_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    _onlyonce: bool = False
    _notify: bool = False
    _scraper_paths: str = None
    _tmdb : TmdbApi = None
    _tmdbscraper : TmdbScraper = None

    def init_plugin(self, config: dict = None):
        self._tmdb = TmdbApi()
        self._tmdbscraper = TmdbScraper(self._tmdb)
        if config:
            self._onlyonce = config.get("onlyonce")
            self._scraper_paths = config.get("scraper_paths")
        run = False
        if self._onlyonce:
            # 执行替换
            run = True
            self._onlyonce = False
        self.__update_config()
        if run:
            self.scraping()

    def scraping(self):
        paths = self._scraper_paths.split("\n")
        scrape_list = []
        for path in paths:
            scraper_path = Path(path)
            if scraper_path.is_file:
                # 單一檔案
                files = [scraper_path]
            else:
                # 資料夾
                files = SystemUtils.list_files(scraper_path, settings.RMT_MEDIAEXT)
            for file in files:
                transferhistorys = TransferHistoryOper().get_by_title(str(file))
                for transferhistory in transferhistorys:
                    scrape_list.append({
                        "src": transferhistory.src,
                        "dest": transferhistory.dest
                    })
        for scrape_item in scrape_list:
            scrape(
                src_path=scrape_item["src"],
                dest_path=scrape_item["dest"],
                tmdbscraper=self._tmdbscraper,
            )

    

    def __update_config(self):
        self.update_config({"onlyonce": self._onlyonce, "notify": self._notify, "scraper_paths": self._scraper_paths})

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlyonce",
                                            "label": "立即运行一次",
                                        },
                                    },
                                
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "notify",
                                            "label": "發送通知",
                                        },
                                    },
                                
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {
                                    "cols": 12,
                                },
                                "content": [
                                    {
                                        "component": "VTextarea",
                                        "props": {
                                            "model": "scraper_paths",
                                            "label": "需要刮削的目錄or路徑",
                                            "rows": 5,
                                            "placeholder": "目錄or路徑 (一行一個)",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ], {"onlyonce": False, "notify": False,"scraper_paths": ""}

    def get_page(self) -> List[dict]:
        pass

    def get_state(self) -> bool:
        return self._onlyonce

    def stop_service(self):
        pass
