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
from app.plugins.mediascraperone.do_scrape import scrape


class MediaScraperOne(_PluginBase):
    # 插件名称
    plugin_name = "一次性刮"
    # 插件描述
    plugin_desc = "一次性刮削繁體中文資訊。"
    # 插件图标
    plugin_icon = "scraper.png"
    # 插件版本
    plugin_version = "0.1"
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

    # 私有属性
    _onlyonce = False
    _tmdbscraper = None
    _scrape_path = ""

    def init_plugin(self, config: dict = None):
        self._tmdb = TmdbApi()
        self._tmdbscraper = TmdbScraper(self._tmdb)
        if config:
            self._onlyonce = config.get("onlyonce")
            self._scrape_path = config.get("scrape_path")

        if self._onlyonce:
            # 执行替换
            if self._scrape_path != "":
                scrape(self._scrape_path, self._tmdbscraper)
            self._onlyonce = False

    def get_state(self) -> bool:
        return self._onlyonce

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
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
                                            "label": "立即執行一次",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 8},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "scrape_path",
                                            "label": "刮削地址",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ], {"enabled": False, "request_method": "POST", "webhook_url": ""}

    def get_page(self) -> List[dict]:
        pass

    def stop_service(self):
        """
        退出插件
        """
        pass
