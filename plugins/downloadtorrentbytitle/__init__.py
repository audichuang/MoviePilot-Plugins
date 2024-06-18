import time
from typing import Any, List, Dict, Tuple

from app.core.config import settings


# from app.modules.emby import Emby
# from app.modules.jellyfin import Jellyfin
# from app.modules.plex import Plex
from app.plugins import _PluginBase

from app.log import logger
from app.db.transferhistory_oper import TransferHistoryOper
from app.utils.system import SystemUtils
from app.core.config import settings
from app.api.endpoints.site import site_resource
from app.api.endpoints.download import add
from pathlib import Path


class DownloadTorrentByTitle(_PluginBase):
    # 插件名称
    plugin_name = "種子下載"
    # 插件描述
    plugin_desc = "根據站點種子標題和副標題下載種子"
    # 插件图标
    plugin_icon = "download.png"
    # 插件版本
    plugin_version = "0.5"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "download_torrent_by_title_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    def init_plugin(self, config: dict = None):
        try:
            self._enable = config.get("enable") if config.get("enable") else False
            self._notify = config.get("notify") if config.get("notify") else False
            self._plugin_key = (
                config.get("plugin_key")
                if config.get("plugin_key")
                else settings.API_TOKEN
            )
        except Exception as e:
            logger.error(f"init_plugin error: {e}")

    def download_torrent(seld, site_id: str, title: str, sub_title: str) -> Any:
        logger.info(
            f"download_torrent: site_id: {site_id}, title: {title}, sub_title: {sub_title}"
        )
        try:
            site_torrents = site_resource(site_id)
        except Exception as e:
            logger.error(f"download_torrent: get site_torrents error: {e}")
            return None
        logger.info(f"site_torrents: {site_torrents}")
        try:
            download_torrent_info = None
            for site_torrent in site_torrents:
                if (
                    site_torrent.title == title
                    and site_torrent.description == sub_title
                ):
                    download_torrent_info = site_torrent
                    break
            if not download_torrent_info:
                return {"code": 404, "msg": "找不到符合標題和副標題的種子"}
            logger.info(f"匹配到的種子訊息: {download_torrent_info}")
        except Exception as e:
            logger.error(f"匹配種子發生錯誤: {e}")
        # 下载种子
        try:
            response = add(torrent_in=download_torrent_info)
            if response.success:
                logger.info(f"download_torrent success: {response.message}")
                return {"code": 200, "msg": "下載成功"}
            else:
                logger.error(f"download_torrent error: {response.message}")
                return {"code": 500, "msg": response.message}
        except Exception as e:
            logger.error(f"download_torrent error: {e}")

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/download_torrent",
                "endpoint": self.download_torrent,
                "methods": ["GET"],
                "summary": "下載種子",
                "description": "根據站點id,標題,副標題下載種子",
            }
        ]

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
                                            "model": "enable",
                                            "label": "啟動",
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
                            },
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "plugin_key",
                                    "label": "插件plugin_key",
                                    "placeholder": "留空默认是mp的api_key",
                                },
                            }
                        ],
                    },
                ],
            }
        ], {
            "enable": self._enable,
            "notify": self._notify,
            "plugin_key": self._plugin_key,
        }

    def get_page(self) -> List[dict]:
        pass

    def get_state(self) -> bool:
        return self._enable

    def stop_service(self):
        pass
