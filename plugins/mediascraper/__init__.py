import time
from typing import Any, List, Dict, Tuple

from app.core.config import settings
from app.core.context import MediaInfo
from app.modules.themoviedb.tmdbapi import TmdbApi
from app.plugins.mediascraper.scraper import TmdbScraper

from app.core.event import eventmanager, Event

# from app.modules.emby import Emby
# from app.modules.jellyfin import Jellyfin
# from app.modules.plex import Plex
from app.plugins import _PluginBase
from app.schemas import TransferInfo, RefreshMediaItem
from app.schemas.types import EventType
from app.log import logger
from app.plugins.mediascraper.do_scrape import scrape


class MediaScraper(_PluginBase):
    # 插件名称
    plugin_name = "刮削繁體中文資訊"
    # 插件描述
    plugin_desc = "入庫後自動刮削繁體中文資訊。"
    # 插件图标
    plugin_icon = "scraper.png"
    # 插件版本
    plugin_version = "1.4"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "media_scraper_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _delay = 0
    _emby = None
    _jellyfin = None
    _plex = None
    _tmdb = None
    _tmdbscraper = None

    def init_plugin(self, config: dict = None):
        self._tmdb = TmdbApi()
        self._tmdbscraper = TmdbScraper(self._tmdb)
        if config:
            self._enabled = config.get("enabled")
            self._delay = config.get("delay") or 0

    def get_state(self) -> bool:
        return self._enabled

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
                                            "model": "enabled",
                                            "label": "启用插件",
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
                                "props": {
                                    "cols": 12,
                                },
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "delay",
                                            "label": "延迟时间（秒）",
                                            "placeholder": "0",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ], {"enabled": False, "delay": 0}

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.TransferComplete)
    def refresh(self, event: Event):
        if not self._enabled:
            return
        event_info: dict = event.event_data
        if not event_info:
            return
        # 入库数据
        transferinfo: TransferInfo = event_info.get("transferinfo")
        mediainfo: MediaInfo = event_info.get("mediainfo")
        try:
            title = mediainfo.title
            year = mediainfo.year
            type = mediainfo.type
            category = mediainfo.category
            target_path = transferinfo.target_path
            src = transferinfo.src
            dest = transferinfo.dest
            path = transferinfo.path
            file_list_new = transferinfo.file_list_new
            logger.info(
                f"title:{title},year:{year},type:{type},category:{category},target_path:{target_path},path:{path},file_list_new:{file_list_new},src:{src},dest:{dest}"
            )
            for file_path in file_list_new:
                scrape(
                    src_path=transferinfo.path,
                    scrape_path=file_path,
                    tmdbscraper=self._tmdbscraper,
                )
        except Exception as e:
            logger.error(f"刮削{transferinfo} {mediainfo}發生錯誤：{e}")

    def stop_service(self):
        """
        退出插件
        """
        pass
