import time
from typing import Any, List, Dict, Tuple

from app.core.config import settings

from app.plugins import _PluginBase

from app.log import logger
from app.db.transferhistory_oper import TransferHistoryOper
from app.chain.transfer import TransferChain
from app.utils.system import SystemUtils
from app.core.config import settings
from pathlib import Path
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
from app.core.event import eventmanager
from app.schemas.types import EventType


class HistoryApi(_PluginBase):
    # 插件名称
    plugin_name = "歷史紀錄接口"
    # 插件描述
    plugin_desc = "多個關於歷史紀錄搜尋的接口"
    # 插件图标
    plugin_icon = "Vertex_B.png"
    # 插件版本
    plugin_version = "1.6"
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
            logger.info(f"已經設定plugin_key: {self._plugin_key}")
        except Exception as e:
            logger.error(f"init_plugin error: {e}")
            return schemas.Response(success=False, message="API密碼錯誤")

    def search_history_by_tmdbid_and_type(
            self, key: str, tmdbid: int, mtype: str, season: str = None, episode: str = None
    ):
        if key != self._plugin_key:
            logger.error(f"download_torrent: plugin_key error: {key}")
            return None
        logger.info(
            f"search_history_by_tmebid_and_type: tmdbid: {tmdbid}, mtype: {mtype}, season: {season}, episode: {episode}"
        )
        m_type = {"tv": "电视剧", "movie": "电影"}.get(mtype)
        if not m_type:
            return schemas.Response(success=False, message="Invalid mtype")
        try:
            if season and episode and m_type == "电视剧":
                # 查詢電視劇某集
                logger.info(f"search_history_by_tmebid_and_type: 電視劇某集")
                result = TransferHistory.list_by(
                    db=Depends(get_db),
                    tmdbid=tmdbid,
                    mtype=m_type,
                    season=season,
                )
                result = [item for item in result if item.episodes == episode]
            elif season and not episode and m_type == "电视剧":
                # 查詢電視劇某季
                logger.info(f"search_history_by_tmebid_and_type: 電視劇某季")
                result = TransferHistory.list_by(
                    db=Depends(get_db), tmdbid=tmdbid, mtype=m_type, season=season
                )
            elif not season and not episode and m_type == "电视剧":
                # 查詢電視劇全部季集數
                logger.info(f"search_history_by_tmebid_and_type: 電視劇全部季集")
                result = TransferHistory.list_by(
                    db=Depends(get_db), tmdbid=tmdbid, mtype=m_type
                )
            else:
                # 查詢電影或電視劇
                logger.info(f"search_history_by_tmebid_and_type: 電影或電視劇")
                result = TransferHistory.list_by(
                    db=Depends(get_db), tmdbid=tmdbid, mtype=m_type
                )

        except Exception as e:
            logger.error(f"search_history_by_tmebid_and_type error: {e}")
            return schemas.Response(success=False, message="查詢歷史紀錄失敗")

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

    def search_history_by_title(
            self, key: str, title: str, page: int = 1, count: int = 30, status: bool = None,
    ):
        if key != self._plugin_key:
            logger.error(f"download_torrent: plugin_key error: {key}")
            return None
        logger.info(
            f"search_history_by_title: title: {title}, page: {page}, count: {count}, status: {status}"
        )
        try:
            result = TransferHistory.list_by_title(
                db=Depends(get_db), title=title, page=page, count=count, status=status)
        except Exception as e:
            logger.info(e)
            return schemas.Response(success=False, message="查詢歷史紀錄失敗")

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

    def history_delete(self, key: str, id: int):
        """
        刪除轉移歷史紀錄

        Args:
            key (str): 插件金鑰
            id (int): 歷史記錄ID

        Returns:
            schemas.Response: 響應結果
        """
        try:
            # 驗證插件金鑰
            if key != self._plugin_key:
                logger.error(f"插件金鑰驗證失敗: 預期 {self._plugin_key}, 實際 {key}")
                return schemas.Response(success=False, msg="插件金鑰驗證失敗")

            logger.info(f"開始刪除歷史記錄 ID: {id}")

            # 獲取歷史記錄
            try:
                history = TransferHistory.get(Depends(get_db), id)
            except Exception as e:
                logger.error(f"查詢歷史記錄失敗: {str(e)}")
                return schemas.Response(success=False, msg=f"查詢歷史記錄失敗: {str(e)}")

            if not history:
                logger.warning(f"歷史記錄不存在: ID {id}")
                return schemas.Response(success=False, msg="記錄不存在")

            # 刪除目標媒體庫文件
            if history.dest:
                try:
                    logger.info(f"正在刪除目標文件: {history.dest}")
                    state, msg = TransferChain().delete_files(Path(history.dest))
                    if not state:
                        logger.error(f"刪除目標文件失敗: {msg}")
                        return schemas.Response(success=False, msg=f"刪除目標文件失敗: {msg}")
                    logger.info(f"目標文件刪除成功: {history.dest}")
                except Exception as e:
                    logger.error(f"刪除目標文件時發生異常: {str(e)}")
                    return schemas.Response(success=False, msg=f"刪除目標文件時發生異常: {str(e)}")

            # 刪除源文件
            if history.src:
                try:
                    logger.info(f"正在刪除源文件: {history.src}")
                    state, msg = TransferChain().delete_files(Path(history.src))
                    if not state:
                        logger.error(f"刪除源文件失敗: {msg}")
                        return schemas.Response(success=False, msg=f"刪除源文件失敗: {msg}")

                    # 發送文件刪除事件
                    try:
                        eventmanager.send_event(
                            EventType.DownloadFileDeleted,
                            {
                                "src": history.src,
                                "hash": history.download_hash
                            }
                        )
                        logger.info(f"已發送文件刪除事件: {history.src}")
                    except Exception as e:
                        logger.error(f"發送文件刪除事件失敗: {str(e)}")
                        # 這裡我們選擇繼續執行，因為這不是關鍵錯誤

                    logger.info(f"源文件刪除成功: {history.src}")
                except Exception as e:
                    logger.error(f"刪除源文件時發生異常: {str(e)}")
                    return schemas.Response(success=False, msg=f"刪除源文件時發生異常: {str(e)}")

            # 刪除數據庫記錄
            try:
                TransferHistory.delete(Depends(get_db), id)
                logger.info(f"成功刪除歷史記錄 ID: {id}")
            except Exception as e:
                logger.error(f"刪除數據庫記錄失敗: {str(e)}")
                return schemas.Response(success=False, msg=f"刪除數據庫記錄失敗: {str(e)}")

            return schemas.Response(success=True, msg="歷史記錄刪除成功")

        except Exception as e:
            logger.error(f"刪除歷史記錄時發生未預期的錯誤: {str(e)}")
            return schemas.Response(success=False, msg=f"刪除歷史記錄時發生未預期的錯誤: {str(e)}")

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/searchhistory",
                "endpoint": self.search_history_by_tmdbid_and_type,
                "methods": ["GET"],
                "summary": "透過tmdbid搜尋歷史紀錄",
                "description": "根據輸入的tmdbid和mtype，查詢歷史紀錄",
            },
            {
                "path": "/searchhistorytitle",
                "endpoint": self.search_history_by_title,
                "methods": ["GET"],
                "summary": "透過關鍵字搜尋歷史紀錄",
                "description": "根據輸入的關鍵字，查詢歷史紀錄",
            },
            {
                "path": "/historydelete",
                "endpoint": self.history_delete,
                "methods": ["GET"],
                "summary": "透過歷史紀錄ID刪除歷史紀錄",
                "description": "根據輸入的歷史紀錄ID，刪除該條歷史紀錄",
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
