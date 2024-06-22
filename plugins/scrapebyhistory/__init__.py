from app.log import logger

try:
    import re
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
    from pathlib import Path

    from app.modules.themoviedb.tmdbapi import TmdbApi
    from app.utils.system import SystemUtils

    from .scraper import TmdbScraper
    from .do_scrape import scrape
except Exception as e:
    logger.error(f"插件導入package失败：{str(e)}")


class ScrapebyHistory(_PluginBase):
    # 插件名称
    plugin_name = "根據歷史紀錄刮削"
    # 插件描述
    plugin_desc = "根據正則表達式週期性刮削該段時間入庫影片，強制取代元數據和圖片"
    # 插件图标
    plugin_icon = "scraper.png"
    # 插件版本
    plugin_version = "0.9"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "scrapebyhistory_"
    # 加载顺序
    plugin_order = 15
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _onlyonce = False
    _cron = None
    _scheduler: Optional[BackgroundScheduler] = None
    _tmdb: TmdbApi = None
    _tmdbscraper: TmdbScraper = None

    def init_plugin(self, config: dict = None):
        try:
            # 停止现有任务
            self.stop_service()

            if config:
                self._tmdb = TmdbApi()
                self._tmdbscraper = TmdbScraper(self._tmdb)
                self._enabled = config.get("enabled")
                self._onlyonce = config.get("onlyonce")
                self._cron = config.get("cron")

                # 加载模块
                if self._enabled or self._onlyonce:
                    # 定时服务
                    self._scheduler = BackgroundScheduler(timezone=settings.TZ)

                    # 立即运行一次
                    if self._onlyonce:
                        logger.info(f"根據歷史紀錄刮削媒體庫，立即運行一次")
                        self._scheduler.add_job(
                            self.refresh,
                            "date",
                            run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                            + timedelta(seconds=3),
                            name="媒體庫元數據",
                        )

                        # 关闭一次性开关
                        self._onlyonce = False

                        # 保存配置
                        self.__update_config()

                    # 周期运行
                    if self._cron:
                        try:
                            self._scheduler.add_job(
                                func=self.refresh,
                                trigger=CronTrigger.from_crontab(self._cron),
                                name="根據歷史紀錄刮削元數據",
                            )
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
            }
        )

    def refresh(self):
        paths = self._get_scrape_paths()
        logger.info(f"開始分析，共有{len(paths)}個資料夾需要刮削")
        scrape_list = []
        for path in paths:
            scraper_path = Path(path)
            # 資料夾
            files = SystemUtils.list_files(scraper_path, settings.RMT_MEDIAEXT)
            for file in files:
                transferhistorys = TransferHistoryOper().get_by_title(str(file))
                for transferhistory in transferhistorys:
                    scrape_list.append(
                        {
                            "src": transferhistory.src,
                            "dest": transferhistory.dest,
                        }
                    )
        logger.info(f"共有{len(scrape_list)}個需要刮削的檔案")
        for scrape_item in scrape_list:
            try:
                response = scrape(
                    src_path=scrape_item["src"],
                    dest_path=Path(scrape_item["dest"]),
                    tmdbscraper=self._tmdbscraper,
                )
                if response.success is False:
                    logger.error(f"刮削 {scrape_item['src']} 失敗: {response.message}")

            except Exception as e:
                logger.error(f"刮削 {scrape_item['src']} 發生錯誤: {e}")
        logger.info("刮削完成")

    def _get_scrape_paths(self):
        """
        刷新媒體庫元數據
        """
        scrape_set = set()
        historys = self._get_historys(self._cron)
        for history in historys:
            try:
                # 匹配包含年份的資料夾名稱
                year_folder = self._extract_year_folder(history.dest)
                scrape_set.add(year_folder)
            except Exception as e:
                logger.error(f"獲取刮削歷史紀錄資料夾發生錯誤：{str(e)}")
        logger.info(f"本次刮削歷史紀錄資料夾數量：{len(scrape_set)}")
        return scrape_set

    def _get_target_date(
        self, cron_expression: str, base_time: datetime = None
    ) -> datetime:
        if base_time is None:
            base_time = datetime.now()

        cron = croniter(cron_expression, base_time)
        cron = croniter(cron_expression, base_time)
        cron.get_prev(datetime)  # 獲取上一次觸發時間

        return cron.get_prev(datetime)

    def _get_historys(self, cron_expression: str) -> bool:
        previous_date = self._get_target_date(cron_expression)
        transferhistorys = TransferHistoryOper().list_by_date(
            previous_date.strftime("%Y-%m-%d %H:%M:%S")
        )
        logger.info(
            f"{previous_date} 之前是否有媒體庫入庫記錄：{len(transferhistorys)}个"
        )
        return transferhistorys

    def _extract_year_folder(self, path):
        # 使用正則表達式來匹配包含年份的資料夾名稱
        match = re.search(r"(/[^/]*\(\d{4}\))", path)
        if match:
            # 提取匹配的資料夾名稱部分
            folder_name = match.group(1)
            # 找到匹配資料夾名稱在原始路徑中的位置
            folder_end_index = path.find(folder_name) + len(folder_name)
            # 返回包含年份的資料夾的完整路徑
            return path[:folder_end_index]
        else:
            return None

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
                                            "label": "启用插件",
                                        },
                                    }
                                ],
                            },
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
                                "props": {
                                    "cols": 12,
                                },
                                "content": [
                                    {
                                        "component": "VAlert",
                                        "props": {
                                            "type": "info",
                                            "variant": "tonal",
                                            "text": "查詢入庫記錄，週期請求媒體服務器元數據刷新接口。注：只支持Emby。",
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
