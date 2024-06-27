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
from app import schemas
from app.chain.download import DownloadChain
from app.chain.media import MediaChain
from app.core.metainfo import MetaInfo
from app.db.models.user import User
from app.db.userauth import get_current_active_user
from fastapi import Depends
from app.db.models.transferhistory import TransferHistory
from fastapi import APIRouter, Depends
from app.db import get_db
from app import schemas


class HistoryApi(_PluginBase):
    # 插件名称
    plugin_name = "歷史紀錄接口"
    # 插件描述
    plugin_desc = "多個關於歷史紀錄搜尋的接口"
    # 插件图标
    plugin_icon = "Vertex_B.png"
    # 插件版本
    plugin_version = "0.5"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "historyapi_"
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

    def search_history_by_tmebid_and_type(self, key: str, tmdbid: int, mtype: str, season: str = None):
        if key != self._plugin_key:
            logger.error(f"download_torrent: plugin_key error: {key}")
            return None
        logger.info(
            f"search_history_by_tmebid_and_type: tmdbid: {tmdbid}, mtype: {mtype}, season: {season}"
        )
        m_type = {"tv": "电视剧", "movie": "电影"}.get(mtype)
        if not m_type:
            return schemas.Response(success=False, message="Invalid mtype")

        result = TransferHistory.list_by(
            db=Depends(get_db), tmdbid=tmdbid, mtype=m_type, season=season
        )

        result_list = [item.to_dict() for item in result]
        total = len(result_list)
        logger.info(f"查詢到的歷史紀錄數量: {total}")
        return schemas.Response(
            success=True,
            data={
                "list": result_list,
                "total": total,
            },
        )

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/searchhistory",
                "endpoint": self.search_history_by_tmebid_and_type,
                "methods": ["GET"],
                "summary": "搜尋歷史紀錄",
                "description": "根據輸入的tmdbid和mtype，查詢歷史紀錄",
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
