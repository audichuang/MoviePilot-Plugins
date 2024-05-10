import sqlite3
from pathlib import Path
from typing import List, Tuple, Dict, Any

from app.core.config import Settings
from app.log import logger
from app.plugins import _PluginBase


class FindHistory(_PluginBase):
    # 插件名称
    plugin_name = "尋找歷史文件"
    # 插件描述
    plugin_desc = "尋找歷史文件"
    # 插件图标
    plugin_icon = "Bookstack_A.png"
    # 插件版本
    plugin_version = "0.5"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "findhistory_"
    # 加载顺序
    plugin_order = 32
    # 可使用的用户级别
    auth_level = 1

    _onlyonce: bool = False
    _link_dirs: str = None

    def init_plugin(self, config: dict = None):
        if config:
            self._onlyonce = config.get("onlyonce")
            self._link_dirs = config.get("link_dirs")

        if self._onlyonce:
            # 执行替换
            self._task()
            self._onlyonce = False
        self.__update_config()

    def _task(self):
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
            transfer_history_dict = {}
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
        for tmdbid, shows in transfer_history_dict.items():
            dict = {}
            for show in shows:
                if show["seasons"] not in dict.keys():
                    dict[show["seasons"]] = []
                if show["download_hash"] not in dict[show["seasons"]]:
                    dict[show["seasons"]].append(show["download_hash"])
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
        try:
            result_dict = {}
            for need_to_tidy_show in need_to_tidy_shows:
                if need_to_tidy_show["tmdbid"] in subscribe_history_dict.keys():
                    list1 = subscribe_history_dict[need_to_tidy_show["tmdbid"]]
                    list2 = need_to_tidy_show["seasons"]
                    # 找到 list2 中存在但 list1 中不存在的元素(並非訂閱的季)
                    not_in_list1 = [x for x in list2 if x not in list1]
                    result_dict[need_to_tidy_show["tmdbid"]] = not_in_list1
        except Exception as e:
            logger.error(f"查询订阅记录失败：{str(e)}")
            return
        logger.info(f"共{len(result_dict)}个电视剧需要整理")
        try:
            for tmdbid, seasons in result_dict.items():
                notify_text = f"{tmdbid} {transfer_history_dict[tmdbid][0]["title"]} 的季{seasons}"
                logger.info(f"需要整理 {notify_text}")
        except Exception as e:
            logger.error(f"生成通知文本失败：{str(e)}")
            return
        logger.info("全部处理完成")

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
        self.update_config({"onlyonce": self._onlyonce, "link_dirs": self._link_dirs})

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
