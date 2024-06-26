import time
from typing import Any, List, Dict, Tuple
import requests
from urllib.parse import quote

from app.core.config import settings
from app.core.context import MediaInfo
from app.core.meta.metabase import MetaBase
from app.modules.themoviedb.tmdbapi import TmdbApi

from app.core.event import eventmanager, Event

from app.modules.emby import Emby
from .emby_user import EmbyUser
from .emby_items import EmbyItems
from .scrape_transfer import Get_TW_info

from app.plugins import _PluginBase
from app.schemas import TransferInfo, RefreshMediaItem
from app.chain.media import MediaChain
from app.schemas.types import EventType, MediaType
from app.log import logger
import queue
import threading


class SendMediaNotificationss(_PluginBase):
    # 插件名称
    plugin_name = "Emby收藏入庫通知"
    # 插件描述
    plugin_desc = "入庫後待Emby加入推送Bark推知給指定的Emby用戶。"
    # 插件图标
    plugin_icon = "Watchtower_A.png"
    # 插件版本
    plugin_version = "1.2"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "sendmedianotificationss_"
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
                logger.info(
                    f"Emby收藏入庫通知插件已啟用，輸入emby用戶名稱和Bark密鑰：{self._emby_bark_dict}"
                )
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
                                "props": {"cols": 12, "md": 6},
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
                                            "rows": 5,
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
        transfer_meta: MetaBase = event_info.get("meta")
        transferinfo: TransferInfo = event_info.get("transferinfo")
        mediainfo: MediaInfo = event_info.get("mediainfo")
        mediainfo_tw = Get_TW_info.get_media_info(mediainfo)
        try:
            type = mediainfo.type
            success = transferinfo.success
            if not success or type == MediaType.MOVIE:
                return
            tmdbid = mediainfo_tw.tmdb_id
            number_of_seasons = transfer_meta.begin_season
            number_of_episodes = transfer_meta.begin_episode
            # logger.info(f"transfer_meta:{transfer_meta}")
            # logger.info(f"transferinfo:{transferinfo}")
            # logger.info(f"mediainfo_tw:{mediainfo_tw}")
            logger.info(
                f"收到入庫資訊：{mediainfo_tw.title} {tmdbid} {number_of_seasons} {number_of_episodes}"
            )
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
                logger.info("本來就存在 不用提醒")
                return
            logger.info("之前沒有 需要提醒用戶")
        except Exception as e:
            logger.error(f"檢查Emby是否有劇集發生錯誤：{e}")
            return

        try:
            # 判斷是否有使用者加入收藏
            logger.info(f"開始檢查是否有使用者收藏")
            # logger.info(f"收藏者：{self._emby_user_favorite_dict}")
            device_keys = []
            try:
                for (
                    username,
                    favorite_tv_tmdbid_list,
                ) in self._emby_user_favorite_dict.items():
                    if len(favorite_tv_tmdbid_list) == 0:
                        continue
                    try:
                        logger.info(f"檢查用戶 {username} 是否收藏 {tmdbid}")
                        logger.info(f"收藏劇集：{favorite_tv_tmdbid_list}")
                        if str(tmdbid) in favorite_tv_tmdbid_list:
                            logger.info(f"用戶 {username} 有收藏 {tmdbid}")
                            device_keys.append(self._emby_bark_dict.get(username))
                    except Exception as e:
                        logger.error(f"判斷使用者{username}是否收藏發生錯誤：{e}")
            except Exception as e:
                logger.error(f"檢查收藏者發生錯誤：{e}")
            logger.info(f"該劇收藏者的Bark密鑰：{device_keys}")
            if len(device_keys) > 0:
                # 有使用者收藏 發送通知
                data = {
                    "media_tmdbid": tmdbid,
                    "media_season_number": number_of_seasons,
                    "media_episode_number": number_of_episodes,
                    "media_title": mediainfo_tw.title,
                    "bark_title": f"已經更新了 {mediainfo_tw.title} 第{number_of_seasons}季第{number_of_episodes}集",
                    "bark_content": " ",
                    "bark_device_keys": device_keys,
                    "bark_image_url": mediainfo_tw.poster_path.replace(
                        "/original/", "/w200/"
                    ),
                }
                logger.info(f"存入佇列：{data}")
                self._download_queue.put(data)
        except Exception as e:
            logger.error(f"存入佇列發生錯誤：{e}")
            return

    def consumer(self):
        logger.info("開始啟用消費者")
        try:
            while True:
                # 從佇列中取出消息
                message = self._download_queue.get()
                logger.info(f"收到入庫處理資訊：{message}")
                logger.info(f"等待三分鐘")
                # 等待入庫 要等大約3分鐘
                time.sleep(180)
                # 可以發送通知了
                try:
                    if not self._emby_items.is_episode_exist(
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
        except Exception as e:
            logger.error(f"佇列取出發生錯誤：{e}")

    def periodic_get_user_favorite(self):
        while True:
            # 每五分鐘查詢一次Emby使用者收藏的劇集
            # logger.info(f"開始查詢Emby使用者收藏的劇集")
            try:
                emby_user_favorit_itemid = self._emby_user.get_all_user_favorite_dict()
                for username, item_id_list in emby_user_favorit_itemid.items():
                    tmdbid_list = []
                    for item_id in item_id_list:
                        try:
                            tmdbid = self._emby_items.get_tmdbid_by_itemid(item_id)
                            if tmdbid:
                                tmdbid_list.append(tmdbid)
                        except Exception as e:
                            logger.error(f"取得劇集tmdbid發生錯誤：{e}")
                    self._emby_user_favorite_dict[username] = tmdbid_list
                logger.info(f"更新Emby使用者收藏：{self._emby_user_favorite_dict}")
            except Exception as e:
                logger.error(f"查詢Emby使用者收藏發生錯誤：{e}")
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
