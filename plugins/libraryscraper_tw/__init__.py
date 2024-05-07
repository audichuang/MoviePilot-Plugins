from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from typing import List, Tuple, Dict, Any

import pytz
import os
import zhconv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.transferhistory_oper import TransferHistoryOper
from app.log import logger
from app.plugins import _PluginBase

from app.plugins.libraryscraper_tw.nfo_file_manager import NfoFileManager
from app.plugins.libraryscraper_tw.media_items.movie import Movie
from app.plugins.libraryscraper_tw.media_items.tv_show import TvShow


class LibraryScraper_Tw(_PluginBase):
    # 插件名称
    plugin_name = "媒體庫刮削(繁體)"
    # 插件描述
    plugin_desc = "定時刮削媒體庫，補齊缺失資訊和圖片，使用繁體中文。"
    # 插件图标
    plugin_icon = "scraper.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "libraryscraper_tw_"
    # 加载顺序
    plugin_order = 7
    # 可使用的用户级别
    user_level = 1

    # 私有属性
    transferhis = None
    _scheduler = None
    # 限速开关
    _enabled = False
    _onlyonce = False
    _cron = None
    _mode = ""
    _scraper_paths = ""
    # 退出事件
    _event = Event()

    def init_plugin(self, config: dict = None):
        # 读取配置
        if config:
            self._enabled = config.get("enabled")
            self._onlyonce = config.get("onlyonce")
            self._cron = config.get("cron")
            self._scraper_paths = config.get("scraper_paths") or ""


        # 停止现有任务
        self.stop_service()

        # 启动定时任务 & 立即运行一次
        if self._enabled or self._onlyonce:
            self.transferhis = TransferHistoryOper()

            if self._onlyonce:
                logger.info(f"媒體庫刮削轉繁體服務，立刻運行一次")
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                self._scheduler.add_job(func=self.__libraryscraper, trigger='date',
                                        run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                        name="媒體庫刮削轉繁體")
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config({
                    "onlyonce": False,
                    "enabled": self._enabled,
                    "cron": self._cron,
                    "scraper_paths": self._scraper_paths
                })
                if self._scheduler.get_jobs():
                    # 启动服务
                    self._scheduler.print_jobs()
                    self._scheduler.start()

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        [{
            "id": "服务ID",
            "name": "服务名称",
            "trigger": "触发器：cron/interval/date/CronTrigger.from_crontab()",
            "func": self.xxx,
            "kwargs": {} # 定时器参数
        }]
        """
        if self._enabled and self._cron:
            return [{
                "id": "LibraryScraper_Tw",
                "name": "媒體庫刮削服務(繁體)",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.__libraryscraper,
                "kwargs": {}
            }]
        elif self._enabled:
            return [{
                "id": "LibraryScraper",
                "name": "媒體庫刮削服務(繁體)",
                "trigger": CronTrigger.from_crontab("0 0 */7 * *"),
                "func": self.__libraryscraper,
                "kwargs": {}
            }]
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'onlyonce',
                                            'label': '立即运行一次',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '执行周期',
                                            'placeholder': '5位cron表达式，留空自动'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'scraper_paths',
                                            'label': '削刮路徑',
                                            'rows': 5,
                                            'placeholder': '每一行一個目錄'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '刮削路径后拼接#电视剧/电影，强制指定该媒体路径媒体类型。'
                                                    '不加默认根据文件名自动识别媒体类型。'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "cron": "0 0 */7 * *",
            "mode": "",
            "scraper_paths": "",
            "err_hosts": ""
        }

    def get_page(self) -> List[dict]:
        pass

    def __libraryscraper(self):
        """
        开始刮削媒体库
        """
        if not self._scraper_paths:
            return
        # 已选择的目录
        paths = self._scraper_paths.split("\n")
        for path in paths:
            if not path:
                continue
            logger.info(f"開始刮削媒體庫路徑：{path} ...")
            # 查找目標目錄中的所有 .nfo 文件
            nfo_files = NfoFileManager.find_nfo_files(path)
            for nfo_file_path in nfo_files:
                try:
                    logger.info(f"開始刮削檔案：{nfo_file_path} ...")
                    file_name = os.path.basename(nfo_file_path)
                    folder_path = os.path.dirname(nfo_file_path)
                    # 判斷是否為電影
                    is_movie_folder = "/电影/" in folder_path
                    # 跳過 BDMV 和 CERTIFICATE 文件夹 (針對原盤)
                    if "/BDMV/" in folder_path or "/CERTIFICATE/" in folder_path:
                        logger.info(f"跳過原盤檔案: {nfo_file_path}")  
                        continue
                    root = NfoFileManager.read_nfo_file(nfo_file_path)
                    properties = NfoFileManager.get_property(root)
                    if is_movie_folder and file_name != "season.nfo" and NfoFileManager.has_tag(nfo_file_path, "<movie>"):
                        # 電影
                        tmdb_id = properties.get("tmdbid")
                        update_dict = Movie.get_movie_nfo_update_dict(tmdb_id, zhconv)
                        logger.info(f"開始刮削 {tmdb_id} 電影：{nfo_file_path} ...")
                        if update_dict:
                            NfoFileManager.modify_nfo_file(nfo_file_path, update_dict)
                    elif not is_movie_folder:
                        # 電視節目
                        if file_name == "tvshow.nfo" and NfoFileManager.has_tag(nfo_file_path, "<tvshow>"):
                            # tvshow
                            tmdb_id = properties.get("tmdbid")
                            logger.info(f"開始刮削 {tmdb_id} 電視劇：{nfo_file_path} ...")
                            update_dict = TvShow.get_tvshow_nfo_update_dict(tmdb_id, zhconv)

                        elif file_name == "season.nfo" and NfoFileManager.has_tag(nfo_file_path, "<season>"):
                            # season
                            tvshow_nfo_path = NfoFileManager.season_nfo_find_tvshow_nfo(nfo_file_path)
                            root = NfoFileManager.read_nfo_file(tvshow_nfo_path)
                            tv_show_properties = NfoFileManager.get_property(root)
                            tmdb_id = tv_show_properties.get("tmdbid")
                            season_number = properties.get("seasonnumber")
                            logger.info(f"開始刮削 {tmdb_id} 第 {season_number} 季：{nfo_file_path} ...")
                            update_dict = TvShow.get_season_nfo_update_dict(tmdb_id, season_number, zhconv)

                        elif NfoFileManager.has_tag(nfo_file_path, "<episodedetails>"):
                            # episode
                            tmdb_id = properties.get("tmdbid")
                            season_number = properties.get("season")
                            episode_number = properties.get("episode")
                            update_dict = TvShow.get_episode_nfo_update_dict(tmdb_id, season_number, episode_number, zhconv)

                        if update_dict:
                            NfoFileManager.modify_nfo_file(nfo_file_path, update_dict)
                except Exception as e:
                    logger.error(f"刮削 {nfo_file_path} 發生錯誤：{str(e)}")
   
            logger.info(f"媒體庫 {path} 刮削完成")
        logger.info(f"媒體庫刮削服務(繁體) 運行完畢")

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._event.set()
                    self._scheduler.shutdown()
                    self._event.clear()
                self._scheduler = None
        except Exception as e:
            print(str(e))