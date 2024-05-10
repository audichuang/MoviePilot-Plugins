import sqlite3
from pathlib import Path
from typing import List, Tuple, Dict, Any

from app.core.config import Settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType


class Tidy(_PluginBase):
    # 插件名称
    plugin_name = "電視劇種子整理"
    # 插件描述
    plugin_desc = "尋找電視劇是否完結且沒訂閱，若非單一種子就必須進行整理種子"
    # 插件图标
    plugin_icon = "Bookstack_A.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "tidy_"
    # 加载顺序
    plugin_order = 32
    # 可使用的用户级别
    auth_level = 1

    _onlyonce: bool = False
    _notify: bool = False
    _link_dirs: str = None

    def init_plugin(self, config: dict = None):
        if config:
            self._onlyonce = config.get("onlyonce")
            self._notify = config.get("notify")
            self._link_dirs = config.get("link_dirs")
        run = False
        if self._onlyonce:
            # 执行替换
            run = True
            self._onlyonce = False
        self.__update_config()
        if run:
            self._task()

    def _task(self):
        db_path = Settings().CONFIG_PATH / "user.db"
        logger.info(f"数据库文件路径：{db_path}")
        try:
            gradedb = sqlite3.connect(db_path)
        except Exception as e:
            logger.error(f"无法打开数据库文件 {db_path}，请检查路径是否正确：{str(e)}")
            return
        transfer_history_dict = {}
        try:
            transfer_history = []
            # 创建游标cursor来执行executeＳＱＬ语句
            logger.info(f"連接到数据库 {db_path}")
            cursor = gradedb.cursor()
            sql = """
                SELECT src, dest, type, category, title, tmdbid, year, seasons, episodes, download_hash
                FROM transferhistory
                WHERE src IS NOT NULL
                AND dest IS NOT NULL
                AND type = '电视剧'
                """
            cursor.execute(sql)
            transfer_history += cursor.fetchall()

            logger.info(f"查询到历史记录{len(transfer_history)}条")
            if not transfer_history:
                logger.error("未获取到历史记录，停止处理")
                return
            subscribe_history_dict = self.get_subsctibe_dict(cursor)
            logger.info(f"电视剧订阅记录 : {subscribe_history_dict}")

            for row in transfer_history:
                tmdbid = row[5]
                transfer_dict = {
                    "src": row[0],
                    "dest": row[1],
                    "type": row[2],
                    "category": row[3],
                    "title": row[4],
                    "tmdbid": row[5],
                    "year": row[6],
                    "seasons": row[7],
                    "episodes": row[8],
                    "download_hash": row[9],
                }
                if tmdbid is None:
                    logger.info(f"跳过无tmdbid的记录：{transfer_dict}")
                    continue
                try:
                    transfer_history_dict[tmdbid].append(transfer_dict)
                except KeyError:
                    transfer_history_dict[tmdbid] = [transfer_dict]
            logger.info(f"共{len(transfer_history_dict)}個電視劇再記錄裡")
        except Exception as e:
            logger.error(f"查询历史记录失败：{str(e)}")
            return
        need_to_tidy_shows = []
        try:
            for tmdbid, shows in transfer_history_dict.items():
                dict = {}
                logger.info(f"处理{tmdbid}的历史记录")
                for show in shows:
                    logger.info(f"处理季度{show['seasons']}的历史记录")
                    if show["seasons"] == "":
                        logger.warning(f"{show['tmdbid']} {show['title']}季度{show['seasons']}为空，跳过")
                        continue
                    season = int(show["seasons"][1:])
                    if season == 0:
                        continue
                    if season not in dict.keys():
                        dict[season] = []
                    if show["download_hash"] is None:
                        logger.warning(f"{show['tmdbid']} {show['title']}季度{show['seasons']}无下载记录，跳过")
                        continue
                    if show["download_hash"] not in dict[season]:
                        dict[season].append(show["download_hash"])
                for season, download_hash_list in dict.items():
                    if len(download_hash_list) > 1:
                        # 多季有不同种子，需要整理      
                        need_to_tidy_shows.append(
                            {
                                "title": shows[0]["title"],
                                "year": shows[0]["year"],
                                "seasons": season,
                                "tmdbid": tmdbid,
                                "torrent_num": len(download_hash_list),
                            }
                        )
                
            logger.info(f"共{len(need_to_tidy_shows)}个需要整理的电视剧")
            logger.info(f"{need_to_tidy_shows}")
            if not need_to_tidy_shows:
                logger.info("无需整理")
                return
        except Exception as e:
            logger.error(f"处理历史记录失败：{str(e)}")
            return
        
        result_dict = {}
        try:
            for need_to_tidy_show in need_to_tidy_shows:
                tmdbid = need_to_tidy_show["tmdbid"]
                if tmdbid in subscribe_history_dict.keys():
                    subscribe_season_list = subscribe_history_dict[tmdbid]
                    if need_to_tidy_show["seasons"] not in subscribe_season_list:
                        try:
                            result_dict[tmdbid].append(need_to_tidy_show["seasons"])
                        except Exception:
                            result_dict[tmdbid] = [need_to_tidy_show["seasons"]]
            if self._notify:
                if len(result_dict) == 0:
                    self.post_message(
                    mtype=NotificationType.MediaServer,
                    title="【電視劇種子】",
                    text=f"沒有需要整理的電視劇",
                    )
                else:
                    self.post_message(
                    mtype=NotificationType.MediaServer,
                    title="【電視劇种子】",
                    text=f"以下电视剧需要整理：\n{result_dict}",
                    )
            logger.info(result_dict)
        except Exception as err:
            logger.info(f"歷史紀錄和訂閱比對發生錯誤:{err}")

    @staticmethod
    def get_subsctibe_dict(cursor):
        """
        获取订阅记录

        :param cursor: 数据库游标
        :return: 订阅记录字典 {tmdbid: [season]}
        """
        sql = """
        SELECT name, tmdbid, year, season
        FROM subscribe
        WHERE tmdbid IS NOT NULL
        AND type = '电视剧'
        """
        cursor.execute(sql)
        subscription_history = []
        subscription_history += cursor.fetchall()
        if not subscription_history:
            logger.error("未获取到订阅记录")
            return {}
        logger.info(f"查询到订阅记录{len(subscription_history)}条")
        subscribe_history_dict = {}
        for row in subscription_history:
            tmdbid = row[1]
            season = row[3]
            try:
                subscribe_history_dict[tmdbid].append(season)
            except KeyError:
                subscribe_history_dict[tmdbid] = [season]
        return subscribe_history_dict

    def __update_config(self):
        self.update_config({"onlyonce": self._onlyonce, "notify": self._notify, "link_dirs": self._link_dirs})

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

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
                                            "model": "onlyonce",
                                            "label": "立即运行一次",
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
                                        "component": "VTextarea",
                                        "props": {
                                            "model": "link_dirs",
                                            "label": "需要恢复的硬链接目录",
                                            "rows": 5,
                                            "placeholder": "硬链接目录 （一行一个）",
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
                                            "text": "根据转移记录中的硬链接恢复源文件",
                                            "style": "white-space: pre-line;",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ], {"onlyonce": False, "link_dirs": ""}

    def get_page(self) -> List[dict]:
        pass

    def get_state(self) -> bool:
        return self._onlyonce

    def stop_service(self):
        pass
