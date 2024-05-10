# import os


# def is_subpath(path, potential_parent):
#     path = os.path.normpath(path)
#     potential_parent = os.path.normpath(potential_parent)
#     return os.path.commonprefix([path, potential_parent]) == potential_parent


# transfer_history_list = [
#     {
#         "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
#         "dest": "/media4/电视剧/欧美剧/寻宝侦探 (2024)/Season 1/寻宝侦探 - S01E11 - 第 11 集.mkv",
#         "type": "电视剧",
#         "category": "欧美剧",
#         "tmdbid": 211288,
#         "year": "2024",
#         "date": "2024-05-06 13:37:13",
#     },
#     {
#         "src": "/media4/源文件/",
#         "dest": "/media4/电视剧/欧美剧/寻宝侦探 (2024)",
#         "type": "电视剧",
#         "category": "欧美剧",
#         "tmdbid": 211288,
#         "year": "2024",
#         "date": "2024-05-06 13:37:13",
#     },
#     {
#         "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
#         "dest": "/media4/电视剧/欧美剧/寻宝侦探 (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
#         "type": "电视剧",
#         "category": "欧美剧",
#         "tmdbid": 211288,
#         "year": "2024",
#         "date": "2024-05-06 13:37:13",
#     },
#     {
#         "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
#         "dest": "/media4/电视剧/欧美剧/AAAA (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
#         "type": "电视剧",
#         "category": "欧美剧",
#         "tmdbid": 211288,
#         "year": "2024",
#         "date": "2024-05-06 13:37:13",
#     },
#     {
#         "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
#         "dest": "/media4/电视剧/欧美剧/CCCC (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
#         "type": "电视剧",
#         "category": "欧美剧",
#         "tmdbid": 211288,
#         "year": "2024",
#         "date": "2024-05-06 13:37:13",
#     },
#     {
#         "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
#         "dest": "/media4/电视剧/台陸劇/寻宝侦探 (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
#         "type": "电视剧",
#         "category": "欧美剧",
#         "tmdbid": 211288,
#         "year": "2024",
#         "date": "2024-05-06 13:37:13",
#     },
# ]
# folderpath_to_process = []
# for history in transfer_history_list:
#     dest = history["dest"]
#     folder_path = os.path.dirname(dest)

#     # 检查是否为已有目录的子目录
#     is_child = False
#     for existing_path in folderpath_to_process:
#         if is_subpath(folder_path, existing_path):
#             is_child = True
#             break

#     if not is_child:
#         folderpath_to_process.append(folder_path)

# # 从最长的路径开始遍历,删除被其他路径包含的路径
# folderpath_to_process.sort(key=len, reverse=True)
# for i in range(len(folderpath_to_process)):
#     for j in range(len(folderpath_to_process)):
#         if i != j and is_subpath(folderpath_to_process[j], folderpath_to_process[i]):
#             folderpath_to_process.pop(j)
#             break

# print(folderpath_to_process)

# folderpath_to_process = ['/media4/动漫/动漫/从Lv2开始开外挂的前勇者候补过着悠哉异世界生活 (2024)/Season 1', '/media4/动漫/动漫/转生为第七王子，随心所欲的魔法学习之路 (2024)/Season 1', '/media4/动漫/动漫/无职转生 ～到了异世界就拿出真本事～ (2021)/Season 2', '/media2/电视剧/欧美剧/吉尔莫·德尔·托罗的奇思妙想 (2022)/Season 1', '/media2/电视剧/欧美剧/恋爱播放列表 Dear.M (2022)/Season 1', '/media2/电视剧/日韩剧/情迷希拉曼地：璀璨名姝 (2024)/Season 1', '/media4/动漫/动漫/狼与香辛料 行商邂逅贤狼 (2024)/Season 1', '/media4/电视剧/国产剧/情深不悔，再爱难为 (2024)/Season 1', '/media4/电视剧/国产剧/请和这样的我恋爱吧 (2024)/Season 1', '/media4/动漫/动漫/通灵王 FLOWERS (2024)/Season 1', '/media4/电视剧/欧美剧/星际迷航：发现号 (2017)/Season 5', '/media4/电视剧/国产剧/披荆斩棘的大小姐 (2024)/Season 1', '/media4/电视剧/国产剧/完全省钱恋爱手册 (2024)/Season 1', '/media2/电视剧/日韩剧/军检察官多伯曼犬 (2022)/Season 1', '/media4/电视剧/日韩剧/搜查班长1958 (2024)/Season 1', '/media4/电视剧/日韩剧/纠正贵司的混乱！ (2024)/Season 1', '/media2/电视剧/国产剧/我的宝贝四千金 (2014)/Season 1', '/media4/动漫/动漫/魔法科高校的劣等生 (2014)/Season 3', '/media4/动漫/动漫/魔法科高校的劣等生 (2014)/Season 2', '/media4/动漫/动漫/魔法科高校的劣等生 (2014)/Season 1', '/media4/电视剧/国产剧/哈尔滨一九四四 (2024)/Season 1', '/media2/电视剧/国产剧/谁都知道我爱你 (2022)/Season 1', '/media4/动漫/动漫/星球大战：帝国传说 (2024)/Season 1', '/media4/电视剧/未分类/兄弟有你就知足 (2024)/Season 1', '/media4/动漫/动漫/月光下的异世界之旅 (2021)/Season 2', '/media4/电视剧/国产剧/生活在别处的我 (2024)/Season 1', '/media2/电视剧/国产剧/我的少年时代 (2024)/Season 1', '/media4/动漫/动漫/王牌酒保 神之杯 (2024)/Season 1', '/media4/电视剧/国产剧/我的神使大人 (2024)/Season 1', '/media4/动漫/动漫/老夫老妻重返青春 (2024)/Season 1', '/media4/电视剧/日韩剧/虽然不是英雄 (2024)/Season 1', '/media4/动漫/动漫/终末列车去哪里？ (2024)/Season 1', '/media/电视剧/欧美剧/奇幻精灵事件簿 (2024)/Season 1', '/media4/电视剧/日韩剧/美女与纯情男 (2024)/Season 1', '/media/电视剧/日韩剧/律师Sodom (2023)/Season 1', '/media2/电视剧/欧美剧/我们是幸运儿 (2024)/Season 1', '/media4/电视剧/欧美剧/莫斯科绅士 (2024)/Season 1', '/media4/动漫/动漫/神渴望着游戏。 (2024)/Season 1', '/media2/电视剧/欧美剧/好想做一次 (2020)/Season 1', '/media2/电视剧/欧美剧/好想做一次 (2020)/Season 2', '/media2/电视剧/欧美剧/好想做一次 (2020)/Season 3', '/media4/电视剧/国产剧/少年巴比伦 (2024)/Season 1', '/media/电视剧/未分类/谁杀了萨拉？ (2021)/Season 2', '/media/电视剧/未分类/谁杀了萨拉？ (2021)/Season 1', '/media/电视剧/日韩剧/杀人者的难堪 (2024)/Season 1', '/media/电视剧/未分类/谁杀了萨拉？ (2021)/Season 3', '/media2/电视剧/欧美剧/好想做一次 (2020)/Season 4', '/media4/电视剧/欧美剧/阿卡普尔科 (2021)/Season 2', '/media4/电视剧/欧美剧/阿卡普尔科 (2021)/Season 3', '/media4/电视剧/欧美剧/阿卡普尔科 (2021)/Season 1', '/media4/电视剧/日韩剧/世子消失了 (2024)/Season 1', '/media/电视剧/欧美剧/去他＊的世界 (2017)/Season 1', '/media/电视剧/欧美剧/去他＊的世界 (2017)/Season 2', '/media4/电视剧/日韩剧/七人的复活 (2024)/Season 1', '/media4/电视剧/日韩剧/背着善宰跑 (2024)/Season 1', '/media/电视剧/国产剧/当我飞奔向你 (2023)/Season 1', '/media4/电视剧/国产剧/我的阿勒泰 (2024)/Season 1', '/media4/电视剧/欧美剧/神探特伦特 (2023)/Season 2', '/media4/电视剧/国产剧/微暗之火 (2024)/Season 1', '/media4/电视剧/欧美剧/小谢尔顿 (2017)/Season 7', '/media4/电视剧/欧美剧/紧急呼救 (2018)/Season 7', '/media4/电视剧/日韩剧/黑幕风云 (2024)/Season 1', '/media4/电视剧/日韩剧/无法告白 (2024)/Season 1', '/media4/电视剧/欧美剧/寻宝侦探 (2024)/Season 1', '/media4/电视剧/欧美剧/神秘博士 (2024)/Season 1', '/media4/电视剧/欧美剧/完全人生 (2024)/Season 1', '/media2/电视剧/国产剧/新闻女王 (2023)/Season 1', '/media4/电视剧/欧美剧/猎金叛途 (2024)/Season 1', '/media4/动漫/动漫/我的英雄学院 (2016)/Season 7', '/media2/电视剧/欧美剧/雪国列车 (2020)/Season 1', '/media2/电视剧/欧美剧/雪国列车 (2020)/Season 2', '/media2/电视剧/欧美剧/雪国列车 (2020)/Season 3', '/media2/电视剧/欧美剧/心灵猎人 (2017)/Season 1', '/media2/电视剧/欧美剧/心灵猎人 (2017)/Season 2', '/media4/电视剧/日韩剧/支配物种 (2024)/Season 1', '/media/电视剧/日韩剧/夜限照相馆 (2024)/Season 1', '/media4/电视剧/日韩剧/366日 (2024)/Season 1', '/media4/电视剧/欧美剧/菜鸟老警 (2018)/Season 6', '/media4/电视剧/欧美剧/人生复本 (2024)/Season 1', '/media4/电视剧/日韩剧/没有秘密 (2024)/Season 1', '/media4/动漫/动漫/摇曳露营△ (2018)/Season 1', '/media4/电视剧/欧美剧/战利品 (2022)/Season 2', '/media4/电视剧/欧美剧/同情者 (2024)/Season 1', '/media4/电视剧/欧美剧/大门奖 (2023)/Season 2', '/media4/动漫/动漫/X战警97 (2024)/Season 1', '/media4/电视剧/综艺/房产兄弟 (2011)/Season 3', '/media4/电视剧/综艺/房产兄弟 (2011)/Season 2', '/media4/电视剧/综艺/房产兄弟 (2011)/Season 4', '/media2/电视剧/综艺/房产兄弟 (2011)/Season 5', '/media/电视剧/国产剧/一念关山 (2023)/Season 1', '/media/电视剧/欧美剧/天外来讯 (2024)/Season 1', '/media/电视剧/欧美剧/布里奇顿 (2020)/Season 2', '/media/电视剧/欧美剧/黑钱胜地 (2017)/Season 2', '/media/电视剧/欧美剧/黑钱胜地 (2017)/Season 1', '/media/电视剧/欧美剧/黑钱胜地 (2017)/Season 3', '/media/电视剧/欧美剧/黑钱胜地 (2017)/Season 4', '/media/电视剧/欧美剧/超感猎杀 (2015)/Season 2', '/media/电视剧/欧美剧/超感猎杀 (2015)/Season 1', '/media4/电视剧/综艺/房产兄弟 (2011)/Season 1', '/media4/电视剧/欧美剧/惨败 (2024)/Season 1', '/media4/动漫/动漫/怪兽8号 (2024)/Season 1', '/media2/电视剧/欧美剧/睡魔 (2022)/Season 1', '/media2/电视剧/欧美剧/无神 (2017)/Season 1', '/media2/电视剧/欧美剧/黑镜 (2011)/Season 1', '/media2/电视剧/欧美剧/黑镜 (2011)/Season 2', '/media2/电视剧/欧美剧/黑镜 (2011)/Season 3', '/media2/电视剧/欧美剧/黑镜 (2011)/Season 4', '/media2/电视剧/欧美剧/黑镜 (2011)/Season 6', '/media2/电视剧/欧美剧/黑镜 (2011)/Season 5', '/media4/电影/外语电影/神奇动物：格林德沃之罪 (2018)', '/media4/电影/外语电影/神奇动物：邓布利多之谜 (2022)', '/media4/电视剧/欧美剧/良医 (2017)/Season 7', '/media4/电视剧/欧美剧/沸点 (2023)/Season 1', '/media4/动漫/动漫/怪物转生 (2024)/Season 1', '/media4/电视剧/国产剧/新生 (2024)/Season 1', '/media/电视剧/欧美剧/纸房子 (2017)/Season 1', '/media/电视剧/欧美剧/邪恶 (2019)/Season 1', '/media/电视剧/欧美剧/邪恶 (2019)/Season 2', '/media/电视剧/欧美剧/邪恶 (2019)/Season 3', '/media/动漫/动漫/忍者神威 (2024)/Season 1', '/media/电视剧/欧美剧/暗黑 (2017)/Season 2', '/media/电视剧/欧美剧/暗黑 (2017)/Season 1', '/media/电视剧/欧美剧/暗黑 (2017)/Season 3', '/media/电视剧/欧美剧/良医 (2017)/Season 1', '/media/电视剧/欧美剧/良医 (2017)/Season 4', '/media/电视剧/欧美剧/良医 (2017)/Season 3', '/media/电视剧/欧美剧/良医 (2017)/Season 2', '/media/电视剧/欧美剧/良医 (2017)/Season 5', '/media/电视剧/欧美剧/良医 (2017)/Season 6', '/media4/电影/外语电影/神奇动物在哪里 (2016)', '/media4/电影/外语电影/哥斯拉-1.0 (2023)', '/media4/电影/外语电影/惊天魔盗团2 (2016)', '/media2/电影/外语电影/对你的想象 (2024)', '/media4/电影/华语电影/黄雀在后！ (2024)', '/media4/电影/外语电影/卡布里尼 (2024)', '/media/电影/外语电影/米勒的女孩 (2024)', '/media4/电影/外语电影/无糖霜 (2024)', '/media2/电影/外语电影/战士 (2023)', '/media4/电影/外语电影/套现 (2024)', '/media/电影/外语电影/路基完 (2024)', '']
# folderpath_to_process.sort(key=len, reverse=True)
# for i in range(len(folderpath_to_process)):
#     for j in range(len(folderpath_to_process)):
#         if i != j and is_subpath(folderpath_to_process[j], folderpath_to_process[i]):
#             folderpath_to_process.pop(j)
#             break

# print(folderpath_to_process)
