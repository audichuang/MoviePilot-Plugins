import time
import requests
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

from fastapi import Depends

from app.db import get_db
from app.modules.emby import Emby
from app.modules.jellyfin import Jellyfin
from app.modules.plex import Plex
from app.db.subscribe_oper import SubscribeOper
from app.chain.subscribe import SubscribeChain, Subscribe
from app.scheduler import Scheduler
from app.schemas.types import MediaType
from app.modules.themoviedb.tmdbapi import TmdbApi


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
    _onlyonce = False
    _notify = False
    _subscribeoper = None
    _subscribechain = None
    _subscribe = None
    _scheduler = None
    _tmdbapi = None

    # 定时器
    _scheduler: Optional[BackgroundScheduler] = None

    def init_plugin(self, config: dict = None):
        # 停止现有任务
        self.stop_service()

        if config:
            self._enabled = config.get("enabled")
            self._cron = config.get("cron")
            self._notify = config.get("notify")
            self._onlyonce = config.get("onlyonce")
            self._subscribeoper = SubscribeOper()
            self._subscribechain = SubscribeChain()
            self._subscribe = Subscribe()
            self._tmdbapi = TmdbApi()
            logger.info(f"self._tmdbapi:{self._tmdbapi} {TmdbApi()}")

            # 加载模块
        if self._enabled:
            # 定时服务
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)

            if self._cron:
                try:
                    self._scheduler.add_job(
                        func=self.drama_detect,
                        trigger=CronTrigger.from_crontab(self._cron),
                        name="刷新剧集元数据",
                    )
                except Exception as err:
                    logger.error(f"定时任务配置错误：{str(err)}")

            if self._onlyonce:
                logger.info(f"刷新最近剧集元数据服务启动，立即运行一次")
                self._scheduler.add_job(
                    func=self.drama_detect,
                    trigger="date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                    name="刷新剧集元数据",
                )
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config(
                    {
                        "onlyonce": False,
                        "cron": self._cron,
                        "enabled": self._enabled,
                        "notify": self._notify,
                    }
                )

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

    # def __get_date(self, offset_day):
    #     now_time = datetime.now()
    #     end_time = now_time + timedelta(days=offset_day)
    #     end_date = end_time.strftime("%Y-%m-%d")
    #     return end_date

    def get_total_episodes(self, tmdbid, season_number):
        try:
            headers = {
                "accept": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NTZhNDFlODE2NTkxMzNjM2M5OTJjZGFiMzZkYjMyMSIsInN1YiI6IjY1ODViMWQ2NzFmMDk1NTdjNTIzZjdjMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Yafqg4nwY-i3mdhinliUOsS9MIKBGeCg2oEIG7y4wuk",
            }
            url = f"https://api.themoviedb.org/3/tv/{tmdbid}/season/{season_number}?language=zh-TW"
            try:
                response = requests.get(url, headers=headers)
                result_dict = response.json()
            except Exception as e:
                logger.error(f"获取{tmdbid}第{season_number}季详情失败：{str(e)}")
                result_dict = {}
            total_episodes = len(result_dict["episodes"])
            return total_episodes
        except Exception as e:
            logger.error(f"獲取{tmdbid}第{season_number}季集数失败：{str(e)}")
            return 0

    def update_subscribe_drama_episode(self, sid, total_episodes):
        self._subscribeoper.update(sid, {"total_episode": total_episodes})
        logger.info(f"刷新{sid}集数成功")

    def subscribe_drama(self, type, tmdbid, year, season, title):
        try:
            mtype = MediaType(type)
            sid, message = self._subscribechain.add(
                mtype=mtype,
                title=str(title),
                year=str(year),
                tmdbid=int(tmdbid),
                season=int(season),
            )
            logger.info(f"添加订阅成功：{message}")
            logger.info(f"订阅ID：{sid}")
        except Exception as e:
            logger.error(f"添加订阅失败：{str(e)}")

    def unsubscribe_drama(self, subscribe_id):
        try:
            db = Depends(get_db)
        except Exception as e:
            logger.error(f"獲取db失败：{str(e)}")
            return
        try:
            subscribe = self._subscribe.get(db, subscribe_id)
            logger.info(f"取消订阅：{subscribe}")
            if subscribe:
                subscribe.delete(db, subscribe_id)
        except Exception as e:
            logger.error(f"取消订阅失败：{str(e)}")

    def refresh_cache(self):
        try:
            self._tmdbapi.clear_cache()
        except Exception as e:
            logger.error(f"清理缓存服务失败：{str(e)}")

    def drama_detect(self):
        all_subscribe = self._subscribeoper.list()
        drama_subscribe = [s for s in all_subscribe if s.type == "电视剧"]
        all_drama_id = [s.id for s in drama_subscribe]
        logger.info(f"訂閱劇集，共{len(all_drama_id)}個訂閱")
        for subscribe_id in all_drama_id:
            subscribe = self._subscribeoper.get(subscribe_id)
            tmdbid = subscribe.tmdbid
            season = subscribe.season
            name = subscribe.name
            year = subscribe.year
            total_epidsodes_old = subscribe.total_episode
            total_episodes = self.get_total_episodes(int(tmdbid), int(season))
            if total_episodes == 0:
                logger.info(
                    f"訂閱id:{subscribe_id} 劇集{name} ({year})第{season}季不存在，跳过"
                )
                continue
            if total_episodes > total_epidsodes_old:
                # 集數不是最新的 重新訂閱
                logger.info(
                    f"{name} ({year})第{season}季最新集数{total_episodes}，目前為{total_epidsodes_old}，需要更新"
                )
                self.unsubscribe_drama(subscribe_id)
                time.sleep(1)
                self.subscribe_drama(
                    type="电视剧",
                    tmdbid=tmdbid,
                    year=year,
                    season=season,
                    title=name,
                )
                logger.info(f"重新訂閱 {name} ({year})第{season}季 成功")
        logger.info("檢查劇集集數完成")

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义远程控制命令
        :return: 命令关键字、事件、描述、附带数据
        """
        return [
            {
                "cmd": "/refreshrecentmeta",
                "event": EventType.PluginAction,
                "desc": "刷新最近元数据",
                "category": "",
                "data": {"action": "refreshrecentmeta"},
            }
        ]

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
