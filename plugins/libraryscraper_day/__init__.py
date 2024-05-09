from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from typing import List, Tuple, Dict, Any

import sqlite3
import time
import pytz
import os
import zhconv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import Settings
from app.core.config import settings
from app.db.transferhistory_oper import TransferHistoryOper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType

from app.plugins.libraryscraper_tw.nfo_file_manager import NfoFileManager
from app.plugins.libraryscraper_tw.media_items.movie import Movie
from app.plugins.libraryscraper_tw.media_items.tv_show import TvShow


class LibraryScraper_Day(_PluginBase):
    # 插件名称
    plugin_name = "歷史記錄刮削媒體庫(繁體)"
    # 插件描述
    plugin_desc = "使用繁體中文依歷史記錄天數刮削媒體庫。"
    # 插件图标
    plugin_icon = "scraper.png"
    # 插件版本
    plugin_version = "1.1"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "libraryscraper_day_"
    # 加载顺序
    plugin_order = 7
    # 可使用的用户级别
    user_level = 1

    # 私有属性
    transferhis = None
    _scheduler = None
    # 限速开关
    _enabled = False
    _notifiy = False
    _onlyonce = False
    _cron = None
    _day = 5
    # 退出事件
    _event = Event()

    def init_plugin(self, config: dict = None):
        # 读取配置
        if config:
            self._enabled = config.get("enabled")
            self._notify = config.get("notify")
            self._onlyonce = config.get("onlyonce")
            self._day = config.get("day")
            self._cron = config.get("cron")

        # 停止现有任务
        self.stop_service()

        # 启动定时任务 & 立即运行一次
        if self._enabled or self._onlyonce:
            self.transferhis = TransferHistoryOper()

            if self._onlyonce:
                logger.info(f"根據歷史記錄刮削媒體庫(繁體)服務，立刻運行一次")
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                self._scheduler.add_job(
                    func=self.__libraryscraper,
                    trigger="date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                    name="歷史記錄刮削媒體庫服務",
                )
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config(
                    {
                        "onlyonce": False,
                        "notify": self._notify,
                        "enabled": self._enabled,
                        "day": self._day,
                        "cron": self._cron,
                    }
                )
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
            return [
                {
                    "id": "LibraryScraper_Tw",
                    "name": "媒體庫刮削服務(繁體)",
                    "trigger": CronTrigger.from_crontab(self._cron),
                    "func": self.__libraryscraper,
                    "kwargs": {},
                }
            ]
        elif self._enabled:
            return [
                {
                    "id": "LibraryScraper",
                    "name": "媒體庫刮削服務(繁體)",
                    "trigger": CronTrigger.from_crontab("0 0 */7 * *"),
                    "func": self.__libraryscraper,
                    "kwargs": {},
                }
            ]
        return []

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
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "啟用插件",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "notify",
                                            "label": "發送通知",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlyonce",
                                            "label": "立刻運行一次",
                                        },
                                    }
                                ],
                            },
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
                                        "component": "VTextField",
                                        "props": {
                                            "model": "cron",
                                            "label": "执行周期",
                                            "placeholder": "5位cron表达式，留空自动",
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
                                        "component": "VTextField",
                                        "props": {
                                            "model": "day",
                                            "label": "幾天的歷史記錄",
                                            "placeholder": "請輸入天數",
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
                                        "component": "VAlert",
                                        "props": {
                                            "type": "info",
                                            "variant": "tonal",
                                            "text": "不刮削原盤影片，請注意目錄結構。",
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
            "cron": "0 0 */7 * *",
            "mode": "",
            "scraper_paths": "",
            "err_hosts": "",
        }

    def get_page(self) -> List[dict]:
        pass

    def __libraryscraper(self):
        """
        开始刮削媒体库
        """
        # 獲取歷史記錄路徑
        paths = self.get_library_scraper_path()
        logger.info(f"成功獲取歷史記錄路徑")
        total_paths = len(paths)
        logger.info(f"處理通知 {self._notify}")
        if self._notify:
            self.post_message(
                mtype=NotificationType.MediaServer,
                title="【媒體庫開始刮削】",
                text=f"總共 {total_paths} 個路徑",
            )
            logger.info(f"成功發送通知")
        for path in paths:
            if not path:
                continue
            total_paths -= 1
            if self._notify:
                self.post_message(
                    mtype=NotificationType.MediaServer,
                    title="【媒體庫刮削】",
                    text=f"開始刮削 {path}",
                )

            logger.info(f"開始刮削媒體庫路徑：{path} ...")
            start_time = time.time()  # 紀錄開始時間

            # 查找目標目錄中的所有 .nfo 文件
            nfo_files = NfoFileManager.find_nfo_files(path)
            for nfo_file_path in nfo_files:
                try:
                    logger.info(f"開始刮削檔案：{nfo_file_path} ...")
                    file_name = os.path.basename(nfo_file_path)
                    folder_path = os.path.dirname(nfo_file_path)
                    # 判斷是否為電影
                    is_movie_folder = "/电影/" in nfo_file_path
                    # 跳過 BDMV 和 CERTIFICATE 文件夹 (針對原盤)
                    if "/BDMV/" in folder_path or "/CERTIFICATE/" in folder_path:
                        logger.info(f"跳過原盤檔案: {nfo_file_path}")
                        continue
                    root = NfoFileManager.read_nfo_file(nfo_file_path)
                    properties = NfoFileManager.get_property(root)
                    if NfoFileManager.has_tag(nfo_file_path, "<movie>"):
                        # 電影
                        tmdb_id = properties.get("tmdbid")
                        update_dict = Movie.get_movie_nfo_update_dict(tmdb_id, zhconv)
                        logger.info(
                            f"開始刮削tmdbid: {tmdb_id} 電影：{nfo_file_path} ..."
                        )
                        NfoFileManager.modify_nfo_file(nfo_file_path, update_dict)

                    elif not is_movie_folder:
                        # 電視節目
                        if file_name == "tvshow.nfo" and NfoFileManager.has_tag(
                            nfo_file_path, "<tvshow>"
                        ):
                            # tvshow
                            tmdb_id = properties.get("tmdbid")
                            logger.info(
                                f"開始刮削tmdbid: {tmdb_id} 電視劇：{nfo_file_path} ..."
                            )
                            update_dict = TvShow.get_tvshow_nfo_update_dict(
                                tmdb_id, zhconv
                            )

                        elif file_name == "season.nfo" and NfoFileManager.has_tag(
                            nfo_file_path, "<season>"
                        ):
                            # season
                            tvshow_nfo_path = NfoFileManager.season_nfo_find_tvshow_nfo(
                                nfo_file_path
                            )
                            root = NfoFileManager.read_nfo_file(tvshow_nfo_path)
                            tv_show_properties = NfoFileManager.get_property(root)
                            tmdb_id = tv_show_properties.get("tmdbid")
                            season_number = properties.get("seasonnumber")
                            logger.info(
                                f"開始刮削tmdbid: {tmdb_id} 第 {season_number} 季：{nfo_file_path} ..."
                            )
                            update_dict = TvShow.get_season_nfo_update_dict(
                                tmdb_id, season_number, zhconv
                            )

                        elif NfoFileManager.has_tag(nfo_file_path, "<episodedetails>"):
                            # episode
                            tmdb_id = properties.get("tmdbid")
                            season_number = properties.get("season")
                            episode_number = properties.get("episode")
                            logger.info(
                                f"開始刮削tmdbid: {tmdb_id} 第 {season_number} 季第 {episode_number} 集：{nfo_file_path} ..."
                            )
                            update_dict = TvShow.get_episode_nfo_update_dict(
                                tmdb_id, season_number, episode_number, zhconv
                            )

                        if update_dict:
                            NfoFileManager.modify_nfo_file(nfo_file_path, update_dict)
                except Exception as e:
                    logger.error(f"刮削 {nfo_file_path} 發生錯誤：{str(e)}")
            end_time = time.time()  # 紀錄結束時間
            logger.info(f"刮削 {path} 完成，耗時 {end_time - start_time:.2f} 秒")
            if self._notify:
                self.post_message(
                    mtype=NotificationType.MediaServer,
                    title="【媒體庫刮削】",
                    text=f"刮削 {path} 完成，耗時 {end_time - start_time:.2f} 秒",
                )
            logger.info(f"媒體庫 {path} 刮削完成")
        logger.info(f"媒體庫刮削服務(繁體) 運行完畢")
        if self._notifiy:
            self.post_message(
                mtype=NotificationType.MediaServer,
                title="【媒體庫刮削】",
                text=f"刮削完成",
            )

    def get_library_scraper_path(self):
        db_path = Settings().CONFIG_PATH / "user.db"
        logger.info(f"数据库文件路径：{db_path}")
        try:
            gradedb = sqlite3.connect(db_path)
        except Exception as e:
            logger.error(f"无法打开数据库文件 {db_path}，请检查路径是否正确：{str(e)}")
            return
        try:
            transfer_history = []
            # 创建游标cursor来执行executeＳＱＬ语句
            logger.info(f"連接到数据库 {db_path}")
            cursor = gradedb.cursor()
            # 获取当前日期
            today = datetime.date.today()

            # 计算指定天數前的日期
            several_days_ago = today - timedelta(days=int(self._day))

            # 将日期格式化为字符串
            several_days_ago_str = several_days_ago.strftime("%Y-%m-%d")

            sql = f"""
            SELECT src, dest, type, category, tmdbid, year, date
            FROM transferhistory
            WHERE src IS NOT NULL
            AND dest IS NOT NULL
            AND date >= '{several_days_ago_str}'
            """
            cursor.execute(sql)
            transfer_history += cursor.fetchall()

            logger.info(f"查询到历史记录{len(transfer_history)}条")
            logger.info(f"{transfer_history}")

            if not transfer_history:
                logger.error("未获取到历史记录，停止处理")
                return
            transfer_history_list = []
            for row in transfer_history:
                transfer_dict = {
                    "src": row[0],
                    "dest": row[1],
                    "type": row[2],
                    "category": row[3],
                    "tmdbid": row[4],
                    "year": row[5],
                    "date": row[6],
                }
                logger.info(f"查询到历史记录{transfer_dict}")
                transfer_history_list.append(transfer_dict)
            logger.info(f"查询到历史记录list共{len(transfer_history_list)}条")
            try:
                folderpath_to_libraryscraper = self.get_process_path_list(
                    transfer_history_list
                )
                logger.info(f"需要刮削的資料夾：{folderpath_to_libraryscraper}")
                logger.info(f"共{len(folderpath_to_libraryscraper)}个需要刮削的資料夾")
                return folderpath_to_libraryscraper
            except Exception as e:
                logger.error(f"获取需要刮削的資料夾失败：{str(e)}")
                return None
        except Exception as e:
            logger.error(f"查询历史记录失败：{str(e)}")
            return None
        finally:
            gradedb.close()
            logger.info(f"关闭数据库 {db_path}")
            logger.info("獲取到需要刮削的資料夾")

    @staticmethod
    def get_process_path_list(transfer_history_list):
        def is_subpath(path, potential_parent):
            path = os.path.normpath(path)
            potential_parent = os.path.normpath(potential_parent)
            return os.path.commonprefix([path, potential_parent]) == potential_parent

        folderpath_to_process = []
        for history in transfer_history_list:
            dest = history["dest"]
            folder_path = os.path.dirname(dest)

            # 检查是否为已有目录的子目录
            is_child = False
            for existing_path in folderpath_to_process:
                if is_subpath(folder_path, existing_path):
                    is_child = True
                    break

            if not is_child:
                folderpath_to_process.append(folder_path)

        # 从最长的路径开始遍历,删除被其他路径包含的路径
        folderpath_to_process.sort(key=len, reverse=True)
        for i in range(len(folderpath_to_process)):
            for j in range(len(folderpath_to_process)):
                if i != j and is_subpath(
                    folderpath_to_process[j], folderpath_to_process[i]
                ):
                    folderpath_to_process.pop(j)
                    break
        return folderpath_to_process

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
