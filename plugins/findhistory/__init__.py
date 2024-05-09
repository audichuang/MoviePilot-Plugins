import sqlite3
from pathlib import Path
from typing import List, Tuple, Dict, Any

import os
import datetime
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
    plugin_version = "0.3"
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
    _day: int = 5

    def init_plugin(self, config: dict = None):
        if config:
            self._onlyonce = config.get("onlyonce")
            self._day = config.get("day")

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
            # 获取当前日期
            today = datetime.date.today()

            # 计算指定天數前的日期
            several_days_ago = today - datetime.timedelta(days=int(self._day))

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
            except Exception as e:
                logger.error(f"获取需要刮削的資料夾失败：{str(e)}")
                return
        except Exception as e:
            logger.error(f"查询历史记录失败：{str(e)}")
            return
        finally:
            gradedb.close()
            logger.info(f"关闭数据库 {db_path}")
        logger.info("全部处理完成")

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

    def __update_config(self):
        self.update_config({"onlyonce": self._onlyonce, "day": self._day})

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
