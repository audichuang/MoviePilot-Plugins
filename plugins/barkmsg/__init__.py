from typing import Any, List, Dict, Tuple
from urllib.parse import quote_plus

from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils


class BarkMsg(_PluginBase):
    # 插件名称
    plugin_name = "Bark通知"
    # 插件描述
    plugin_desc = "使用Bark發送通知到ios裝置。"
    # 插件图标
    plugin_icon = "Bark_A.png"
    # 插件版本
    plugin_version = "1.3"
    # 插件作者
    plugin_author = "audichuang"
    # 作者主页
    author_url = "https://github.com/audichuang"
    # 插件配置项ID前缀
    plugin_config_prefix = "barkmsg_"
    # 加载顺序
    plugin_order = 27
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _server = None
    _apikey = None
    _params = None
    _icon_url = None
    _msgtypes = []

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._msgtypes = config.get("msgtypes") or []
            self._server = config.get("server")
            self._apikey = config.get("apikey")
            self._params = config.get("params")
            self._icon_url = config.get("icon_url")

    def get_state(self) -> bool:
        return self._enabled and (True if self._server and self._apikey else False)

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        # 编历 NotificationType 枚举，生成消息类型选项
        MsgTypeOptions = []
        for item in NotificationType:
            MsgTypeOptions.append({
                "title": item.value,
                "value": item.name
            })
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
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'server',
                                            'label': '服务器',
                                            'placeholder': 'https://api.day.app',
                                        }
                                    }
                                ]
                            },
                            # {
                            #     'component': 'VCol',
                            #     'props': {
                            #         'cols': 12,
                            #         'md': 4
                            #     },
                            #     'content': [
                            #         {
                            #             'component': 'VTextField',
                            #             'props': {
                            #                 'model': 'apikey',
                            #                 'label': '密钥',
                            #                 'placeholder': '',
                            #             }
                            #         }
                            #     ]
                            # },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'params',
                                            'label': '附加参数',
                                            'placeholder': '',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'icon_url',
                                            'label': '圖標網址',
                                            'placeholder': '',
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
                                            'model': 'apikey',
                                            'label': '密钥',
                                            'rows': 2,
                                            'placeholder': '用,隔開多個token',
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
                                        'component': 'VSelect',
                                        'props': {
                                            'multiple': True,
                                            'chips': True,
                                            'model': 'msgtypes',
                                            'label': '消息类型',
                                            'items': MsgTypeOptions
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
                                            'text': '圖標網址可以改變Bark消息的圖標，留空則使用預設圖標。'
                                        }
                                    }
                                ]
                            },
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
                                            'text': '密钥如果有多裝置可以用,隔開，例如：1234567890,1234567891，每個裝置都會收到通知。'
                                        }
                                    }
                                ]
                            },
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            'msgtypes': [],
            'server': 'https://api.day.app',
            'apikey': '',
            'params': ''
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.NoticeMessage)
    def send(self, event: Event):
        """
        消息发送事件
        """
        if not self.get_state():
            return

        if not event.event_data:
            return

        msg_body = event.event_data
        # 渠道
        channel = msg_body.get("channel")
        if channel:
            return
        # 类型
        msg_type: NotificationType = msg_body.get("type")
        # 标题
        title = msg_body.get("title")
        # 文本
        text = msg_body.get("text")

        if not title and not text:
            logger.warn("标题和内容不能同时为空")
            return

        if (msg_type and self._msgtypes
                and msg_type.name not in self._msgtypes):
            logger.info(f"消息类型 {msg_type.value} 未开启消息发送")
            return
        if self._icon_url is None:
            logger.warn("未配置消息图标")
        keys = [key.strip() for key in self._apikey.split(",") if key.strip()]
        if not keys:
            logger.warn("未配置Bark密钥")
        logger.info(f"共配置{len(keys)}个Bark密钥")
        

        try:
            for apikey in keys:
                if not self._server or not apikey:
                    return False, "参数未配置"
                sc_url = "%s/%s/%s/%s" % (self._server, apikey, quote_plus(title), quote_plus(text))
                if self._params:
                    sc_url = "%s?%s" % (sc_url, self._params)
                    if self._icon_url:
                        sc_url = sc_url + f"&icon={self._icon_url}"
                else:
                    if self._icon_url:
                        sc_url = sc_url + f"?icon={self._icon_url}"
                res = RequestUtils().post_res(sc_url)
                if res and res.status_code == 200:
                    ret_json = res.json()
                    code = ret_json['code']
                    message = ret_json['message']
                    if code == 200:
                        logger.info("Bark消息发送成功")
                    else:
                        logger.warn(f"Bark消息发送失败：{message}")
                elif res is not None:
                    logger.warn(f"Bark消息发送失败，错误码：{res.status_code}，错误原因：{res.reason}")
                else:
                    logger.warn(f"Bark消息发送失败：未获取到返回信息")
        except Exception as msg_e:
            logger.error(f"Bark消息发送失败：{str(msg_e)}")

    def stop_service(self):
        """
        退出插件
        """
        pass