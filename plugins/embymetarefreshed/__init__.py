from app.log import logger
try:
    from datetime import datetime, timedelta
    from typing import Optional, Any, List, Dict, Tuple

    import pytz
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    from app.db.transferhistory_oper import TransferHistoryOper
    from app.core.config import settings

    from app.plugins import _PluginBase
    from app.modules.emby import Emby
    from app.schemas.types import EventType
    from croniter import croniter
except Exception as e:
    logger.error(f"插件導入package失败：{str(e)}")


class EmbyMetaRefreshed(_PluginBase):
    # 插件名称
    plugin_name = "Emby媒體庫刷新"
    # 插件描述
    plugin_desc = "若有入庫，定時刷新Emby媒體元數據"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/thsrite/MoviePilot-Plugins/main/icons/emby-icon.png"
    # 插件版本
    plugin_version = "1.2"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "embymetarefreshed_"
    # 加载顺序
    plugin_order = 15
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _onlyonce = False
    _cron = None
    _EMBY_HOST = settings.EMBY_HOST
    _EMBY_APIKEY = settings.EMBY_API_KEY
    _scheduler: Optional[BackgroundScheduler] = None

    def init_plugin(self, config: dict = None):
        try:
            # 停止现有任务
            self.stop_service()

            if config:
                self._enabled = config.get("enabled")
                self._onlyonce = config.get("onlyonce")
                self._cron = config.get("cron")

                if self._EMBY_HOST:
                    if not self._EMBY_HOST.endswith("/"):
                        self._EMBY_HOST += "/"
                    if not self._EMBY_HOST.startswith("http"):
                        self._EMBY_HOST = "http://" + self._EMBY_HOST

                # 加载模块
                if self._enabled or self._onlyonce:
                    # 定时服务
                    self._scheduler = BackgroundScheduler(timezone=settings.TZ)

                    # 立即运行一次
                    if self._onlyonce:
                        logger.info(f"媒體庫元數據刷新服務啓動，立即運行一次")
                        self._scheduler.add_job(self.refresh, 'date',
                                                run_date=datetime.now(
                                                    tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                                name="媒體庫元數據")

                        # 关闭一次性开关
                        self._onlyonce = False

                        # 保存配置
                        self.__update_config()

                    # 周期运行
                    if self._cron:
                        try:
                            self._scheduler.add_job(func=self.refresh,
                                                    trigger=CronTrigger.from_crontab(self._cron),
                                                    name="媒體庫元數據")
                        except Exception as err:
                            logger.error(f"定時任務配置錯誤：{str(err)}")
                            # 推送實時消息
                            self.systemmessage.put(f"執行週期配置錯誤：{err}")

                    # 啓動任務
                    if self._scheduler.get_jobs():
                        self._scheduler.print_jobs()
                        self._scheduler.start()
        except Exception as e:
            logger.error(f"插件初始化失敗：{str(e)}")

    def get_state(self) -> bool:
        return self._enabled

    def __update_config(self):
        self.update_config(
            {
                "onlyonce": self._onlyonce,
                "cron": self._cron,
                "enabled": self._enabled,
                "days": self._days
            }
        )

    def refresh(self):
        """
        刷新媒體庫元數據
        """
        try:
            logger.info("開始執行Emby媒體庫元數據刷新")
            if "emby" not in settings.MEDIASERVER:
                logger.error("未配置Emby媒體服務器")
                return
            if not self._is_need_refresh():
                logger.info("不需要刷新媒體庫元數據")
                return
        except Exception as e:
            logger.error(f"判斷是否刷新元數據失敗：{str(e)}")
            return
        try:
            if Emby().refresh_root_library():
                logger.info("刷新媒體庫元數據成功")
            else:
                logger.error("刷新媒體庫元數據失敗")
            logger.info("Emby媒體庫元數據刷新完成")
        except Exception as e:
            logger.error(f"刷新媒體庫元數據失敗：{str(e)}")
        # # 获取days内入库的媒体
        # current_date = datetime.now()
        # # 计算几天前的日期
        # target_date = current_date - timedelta(days=int(self._days))
        # transferhistorys = TransferHistoryOper().list_by_date(target_date.strftime('%Y-%m-%d'))
        # if not transferhistorys:
        #     logger.error(f"{self._days}天内没有媒体库入库记录")
        #     return

        # logger.info(f"开始刷新媒体库元数据，最近{self._days}天内入库媒体：{len(transferhistorys)}个")
        # # 刷新媒体库
        # for transferinfo in transferhistorys:
        #     self.__refresh_emby(transferinfo)
        # logger.info(f"刷新媒体库元数据完成")
        
        
    def _get_target_date(self, cron_expression: str, base_time: datetime = None) -> datetime:
        if base_time is None:
            base_time = datetime.now()

        cron = croniter(cron_expression, base_time)
        previous_date = cron.get_prev(datetime)

        return previous_date


    def _is_need_refresh(self, cron_expression: str) -> bool:
        previous_date = self._get_target_date(cron_expression)
        transferhistorys = TransferHistoryOper().list_by_date(
            previous_date.strftime("%Y-%m-%d %H:%M:%S")
        )
        logger.info(f"{previous_date} 之前是否有媒體庫入庫記錄：{len(transferhistorys)}个")
        if len(transferhistorys) == 0:
            return False

        return True
    
    

    

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
                            },
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
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
                        ],
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
                                            'text': '查詢入庫記錄，週期請求媒體服務器元數據刷新接口。注：只支持Emby。'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ],
            }
        ], {
            "enabled": False,
            "onlyonce": False,
            "cron": "5 1 * * *",
        }

    def get_page(self) -> List[dict]:
        pass

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error("退出插件失败：%s" % str(e))