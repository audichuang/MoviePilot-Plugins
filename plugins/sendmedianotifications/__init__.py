import time
from typing import Any, List, Dict, Tuple
import requests
from urllib.parse import quote

from app.core.config import settings
from app.core.context import MediaInfo
from app.modules.themoviedb.tmdbapi import TmdbApi

from app.core.event import eventmanager, Event

from app.modules.emby import Emby
from app.plugins.sendmedianotifications.emby_user import EmbyUser
from app.plugins.sendmedianotifications.emby_items import EmbyItems

from app.plugins import _PluginBase
from app.schemas import TransferInfo, RefreshMediaItem
from app.chain.media import MediaChain
from app.schemas.types import EventType, MediaType
from app.log import logger
import queue
import threading


class SendMediaNotifications(_PluginBase):
    # 插件名称
    plugin_name = "Emby收藏入庫通知"
    # 插件描述
    plugin_desc = "入庫後待Emby加入推送Bark推知給指定的Emby用戶。"
    # 插件图标
    plugin_icon = "Watchtower_A.png"
    # 插件版本
    plugin_version = "0.8"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "sendmedianotifications_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _emby_bark_input = ""
    _emby = None
    _emby_user = None
    _emby_items = None
    _emby_user_favorite_dict = {}
    _download_queue = None
    _bark_server = ""
    _emby_bark_dict = {}

    def init_plugin(self, config: dict = None):
        try:
            self._download_queue = queue.Queue()
            self._emby_bark_dict = {}
            self._emby_user_favorite_dict = {}
            self._emby = Emby()
            self._emby_user = EmbyUser()
            self._emby_items = EmbyItems()
        except Exception as e:
            logger.error(f"初始化參數發生錯誤：{e}")
        try:
            # 啟動消費者線程
            consumer_thread = threading.Thread(target=self.consumer)
            consumer_thread.start()
            # 啟動定期查找Emby使用者收藏的劇
            periodic_get_user_favorite_thread = threading.Thread(
                target=self.periodic_get_user_favorite, daemon=True
            )
            periodic_get_user_favorite_thread.start()
        except Exception as e:
            logger.error(f"啟動線程發生錯誤：{e}")

        try:
            if config:
                self._enabled = config.get("enabled")
                # emby_username:bark_device_key
                self._emby_bark_input = config.get("emby_bark_input") or ""
                self._bark_server = config.get("bark_server") or ""
                people = self._emby_bark_input.split("\n")
                for person in people:
                    if person is None or person == "" or ":" not in person:
                        continue
                    username, bark_device_key = person.split(":")
                    self._emby_bark_dict[username] = bark_device_key
        except Exception as e:
            logger.error(f"讀取配置發生錯誤：{e}")

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
                                            "label": "啟用插件",
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
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "bark_server",
                                            "label": "Bark服務器",
                                            "placeholder": "https://api.day.app",
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
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VTextarea",
                                        "props": {
                                            "model": "emby_bark_input",
                                            "label": "emby用戶名稱和Bark密鑰",
                                            "rows": 2,
                                            "placeholder": "每一行一個用戶，格式：用戶名稱:Bark密鑰",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "emby_bark_input": self._emby_bark_input,
            "bark_server": self._bark_server,
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.TransferComplete)
    def provider(self, event: Event):
        if not self._enabled:
            return
        event_info: dict = event.event_data
        if not event_info:
            return
        # 入库数据
        transferinfo: TransferInfo = event_info.get("transferinfo")
        mediainfo: MediaInfo = event_info.get("mediainfo")
        try:
            type = mediainfo.type
            success = transferinfo.success
            if not success or type == MediaType.MOVIE:
                return
            tmdbid = mediainfo.tmdb_id
            number_of_seasons = mediainfo.number_of_seasons
            number_of_episodes = mediainfo.number_of_episodes
        except Exception as e:
            logger.error(f"解析資料發生錯誤：{e}")
            return
        try:
            # 判斷該轉移是否本來就存在於Emby
            if self._emby_items.is_episode_exist(
                tmdbid=tmdbid,
                season_number=number_of_seasons,
                episode_number=number_of_episodes,
            ):
                # 本來就存在 不用提醒
                return
        except Exception as e:
            logger.error(f"檢查Emby是否有劇集發生錯誤：{e}")
            return
        try:
            # 判斷是否有使用者加入收藏
            device_keys = []
            for (
                username,
                favorite_tv_tmdbid_list,
            ) in self._emby_user_favorite_dict.items():
                if tmdbid in favorite_tv_tmdbid_list:
                    device_keys.append(self._emby_bark_dict.get(username))
            if len(device_keys) > 0:
                # 有使用者收藏 發送通知
                data = {
                    "media_tmdbid": tmdbid,
                    "media_season_number": number_of_seasons,
                    "media_episode_number": number_of_episodes,
                    "media_title": mediainfo.title,
                    "bark_title": f"{mediainfo.title} 有新增的集數",
                    "bark_content": f"季數：{number_of_seasons}\n集數：{number_of_episodes}",
                    "bark_device_keys": device_keys,
                    "bark_image_url": mediainfo.poster_path.replace(
                        "/original/", "/w200/"
                    ),
                }
                logger.info(f"存入佇列：{data}")
                self._download_queue.put(data)
        except Exception as e:
            logger.error(f"存入佇列發生錯誤：{e}")

    def consumer(self):
        while True:
            # 從佇列中取出消息
            message = self._download_queue.get()
            logger.info(f"收到入庫處理資訊：{message}")
            # 等待入庫 要等大約3分鐘
            time.sleep(180)
            # 可以發送通知了
            try:
                if self._emby_items.is_episode_exist(
                    tmdbid=message.get("media_tmdbid"),
                    season_number=message.get("media_season_number"),
                    episode_number=message.get("media_episode_number"),
                ):
                    # 還沒進來 等一段時間
                    logger.info(
                        f"劇集 {message.get('media_title')} 第{message.get('media_season_number')}季第{message.get('media_episode_number')}集 未進入Emby，等待30秒"
                    )
                    time.sleep(60)
                for bark_device_key in message.get("bark_device_keys"):
                    self.bark_send_message(
                        server_url=self._bark_server,
                        token=bark_device_key,
                        title=message.get("bark_title"),
                        content=message.get("bark_content"),
                        icon=message.get("bark_image_url"),
                    )

            except Exception as e:
                logger.error(f"Bark發送失敗：{e}")

            # 通知佇列此消息已處理
            self._download_queue.task_done()

    def periodic_get_user_favorite(self):
        while True:
            # 每五分鐘查詢一次Emby使用者收藏的劇集
            self._emby_user_favorite_dict = self._emby_user.get_user_favorite_dict()
            time.sleep(300)  # 300秒 = 5分鐘

    def bark_send_message(self, server_url, token, title, content, icon):
        if not server_url or server_url == "":
            logger.error(f"Bark服務器地址未設定")
            return
        encoded_title = quote(title, encoding="utf-8")
        encoded_content = quote(content, encoding="utf-8")

        icon_url = icon if "http" in icon else None
        # 基本的 base_url
        base_url = f"{server_url}/{token}/{encoded_title}/{encoded_content}"
        if icon_url:
            base_url += f"?icon={icon_url}"
        response = requests.get(base_url)
        if response.status_code != 200:
            logger.error(f"Bark推送 {token} 失敗: {response.text}")
        else:
            logger.info(f"Bark推送 {token} 成功")

    def stop_service(self):
        """
        退出插件
        """
        pass
