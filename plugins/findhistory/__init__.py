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
    plugin_version = "0.2"
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
        db_path = Settings().CONFIG_PATH / 'user.db'
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
            sql = '''
                    SELECT
                        src,
                        dest,
                        type,
                        category,
                        tmdbid,
                        year,
                        date
                    FROM
                        transferhistory  
                    WHERE
                        src IS NOT NULL
                        AND dest IS NOT NULL
                        AND date >= DATE_SUB(NOW(), INTERVAL 5 DAY)
                        '''
            cursor.execute(sql)
            transfer_history += cursor.fetchall()
            
            logger.info(f"查询到历史记录{len(transfer_history)}条")
            cursor.close()

            if not transfer_history:
                logger.error("未获取到历史记录，停止处理")
                return
            transfer_history = []
            for row in cursor.fetchall():
                transfer_dict = {
                    'src': row[0],
                    'dest': row[1],
                    'type': row[2],
                    'category': row[3],
                    'tmdbid': row[4],
                    'year': row[5],
                    'date': row[6]
                }
                transfer_history.append(transfer_dict)
            # 使用logger.info逐行输出查询结果
            for row_data in transfer_history:
                logger.info(row_data)
        except Exception as e:
            logger.error(f"查询历史记录失败：{str(e)}")
            return
        finally:
            gradedb.close()

        # for history in transfer_history:
        #     src = history[0]
        #     dest = history[1]
        #     # 判断源文件是否存在
        #     if Path(src).exists():
        #         logger.warn(f"源文件{src}已存在，跳过处理")
        #         continue
        #     # 源文件不存在，目标文件也不存在，跳过
        #     if not Path(dest).exists():
        #         logger.warn(f"源文件{src}不存在且硬链文件{dest}不存在，跳过处理")
        #         continue
        #     # 目标文件硬链回源文件
        #     Path(src).hardlink_to(dest)
        #     logger.info(f"硬链文件{dest}重新链接回源文件{src}")

        logger.info("全部处理完成")

    def __update_config(self):
        self.update_config({
            "onlyonce": self._onlyonce,
            "link_dirs": self._link_dirs
        })

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

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
                                    'cols': 12,
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'link_dirs',
                                            'label': '需要恢复的硬链接目录',
                                            'rows': 5,
                                            'placeholder': '硬链接目录 （一行一个）'
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
                                            'text': '根据转移记录中的硬链接恢复源文件',
                                            'style': 'white-space: pre-line;'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "onlyonce": False,
            "link_dirs": ""
        }

    def get_page(self) -> List[dict]:
        pass

    def get_state(self) -> bool:
        return self._onlyonce

    def stop_service(self):
        pass