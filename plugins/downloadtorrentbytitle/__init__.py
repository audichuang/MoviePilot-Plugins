import time
from typing import Any, List, Dict, Tuple

from app.core.config import settings

from app.plugins import _PluginBase

from app.log import logger
from app.db.transferhistory_oper import TransferHistoryOper
from app.utils.system import SystemUtils
from app.core.config import settings
from app.api.endpoints.site import site_resource


from app.core.context import TorrentInfo, Context
from app.core.context import TorrentInfo, Context
from app import schemas
from app.chain.download import DownloadChain
from app.chain.media import MediaChain
from app.core.metainfo import MetaInfo
from app.db.models.user import User
from app.db.userauth import get_current_active_user
from fastapi import Depends


class DownloadTorrentByTitle(_PluginBase):
    # 插件名称
    plugin_name = "種子下載"
    # 插件描述
    plugin_desc = "根據站點種子標題和副標題下載種子"
    # 插件图标
    plugin_icon = "download.png"
    # 插件版本
    plugin_version = "1.5"
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

    _enable: bool = False
    _notify: bool = False
    _plugin_key: str = ""

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
            return schemas.Response(success=False, message="API密碼錯誤")

    def download_torrent(
        self, key: str, site_id: str, title: str, sub_title: str
    ) -> Any:
        if key != self._plugin_key:
            logger.error(f"download_torrent: plugin_key error: {key}")
            return None
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
                    site_torrent["title"] == title
                    and site_torrent["description"] == sub_title
                ):
                    download_torrent_info = site_torrent
                    break
            if not download_torrent_info:
                logger.error(f"找不到符合標題和副標題的種子")
        except Exception as e:
            logger.error(f"匹配種子發生錯誤: {e}")
        logger.info(f"匹配到的種子訊息: {download_torrent_info}")
        # 下载种子
        try:
            torrentinfo = TorrentInfo()
            torrentinfo.from_dict(download_torrent_info)
            current_user = Depends(get_current_active_user)
            logger.info(f"current_user:{current_user}")
        except Exception as e:
            logger.error(f"下载种子初始化失败: {e}")
        try:
            # 元数据
            metainfo = MetaInfo(
                title=torrentinfo.title, subtitle=torrentinfo.description
            )
        except Exception as e:
            logger.error(f"下载种子元数据初始化失败: {e}")
        try:
            # 媒体信息
            mediainfo = MediaChain().recognize_media(meta=metainfo)
            if not mediainfo:
                logger.error(f"無法識別媒體訊息")
        except Exception as e:
            logger.error(f"媒體信息识别失败: {e}")
        logger.info(f"媒體信息: {mediainfo}")
        try:
            # 上下文
            context = Context(
                meta_info=metainfo, media_info=mediainfo, torrent_info=torrentinfo
            )
        except Exception as e:
            logger.error(f"上下文初始化失败: {e}")
        logger.info(f"上下文信息: {context}")
        try:
            did = DownloadChain().download_single(context=context, username="admin")
            if not did:
                logger.error(f"下載種子失敗")
                return schemas.Response(success=False, message="下載種子失敗")
            logger.info(f"下載種子成功, did: {did}")
            return schemas.Response(success=True, message="下載種子成功")
        except Exception as e:
            logger.error(f"下载种子失败: {e}")

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
