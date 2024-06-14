import time
from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.event import eventmanager, Event
from app.core.config import settings
from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple, Optional
from app.log import logger
from app.schemas.types import EventType, NotificationType


from app.db.subscribe_oper import SubscribeOper


class RefreshEpisode(_PluginBase):
    # 插件名称
    plugin_name = "訂閱集數更新"
    # 插件描述
    plugin_desc = "刷新訂閱劇集最新集數"
    # 插件图标
    plugin_icon = "Bookstack_A.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "refreshepisode_"
    # 加载顺序
    plugin_order = 99
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    # 任务执行间隔
    _cron = None
    _offset_days = "0"
    _onlyonce = False
    _notify = False
    _subscribeoper = None

    # 定时器
    _scheduler: Optional[BackgroundScheduler] = None

    def init_plugin(self, config: dict = None):
        # 停止现有任务
        self.stop_service()

        if config:
            self._enabled = config.get("enabled")
            self._cron = config.get("cron")
            self._offset_days = config.get("offset_days")
            self._notify = config.get("notify")
            self._onlyonce = config.get("onlyonce")
            self._subscribeoper = SubscribeOper()

            # 加载模块
        if self._enabled:
            # 定时服务
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)

            if self._cron:
                try:
                    self._scheduler.add_job(
                        func=self.update_drama_episode,
                        trigger=CronTrigger.from_crontab(self._cron),
                        name="刷新劇集訂閱總集數",
                    )
                except Exception as err:
                    logger.error(f"定时任务配置错误：{str(err)}")

            if self._onlyonce:
                logger.info(f"刷新劇集訂閱總集束服務啟動，立即運行一次")
                self._scheduler.add_job(
                    func=self.refresh_recent,
                    trigger="date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                    name="刷新劇集訂閱總集數",
                )
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config(
                    {
                        "onlyonce": False,
                        "cron": self._cron,
                        "enabled": self._enabled,
                        "offset_days": self._offset_days,
                        "notify": self._notify,
                    }
                )

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

    def update_drama_episode(self):
        all_subscribe = self._subscribeoper.list()
        logger.info(f"訂閱集數更新服务，共{len(all_subscribe)}个订阅")
        logger.info(f"{all_subscribe}")
        drama_subscribe = [s for s in all_subscribe if s.get("type") == "电视剧"]
        all_drama_id = [s.get("id") for s in drama_subscribe]
        logger.info(f"訂閱劇集，共{len(all_drama_id)}个订阅")
        logger.info(f"{type(all_drama_id[0])}")

    def get_state(self) -> bool:
        return self._enabled

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
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
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
                                            "label": "开启通知",
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
                                            "label": "立即运行一次",
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
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {"model": "cron", "label": "执行周期"},
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "offset_days",
                                            "label": "几天内",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        ], {"enabled": False, "request_method": "POST", "webhook_url": ""}

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