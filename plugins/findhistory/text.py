import os


def is_subpath(path, potential_parent):
    path = os.path.normpath(path)
    potential_parent = os.path.normpath(potential_parent)
    return os.path.commonprefix([path, potential_parent]) == potential_parent


transfer_history_list = [
    {
        "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
        "dest": "/media4/电视剧/欧美剧/寻宝侦探 (2024)/Season 1/寻宝侦探 - S01E11 - 第 11 集.mkv",
        "type": "电视剧",
        "category": "欧美剧",
        "tmdbid": 211288,
        "year": "2024",
        "date": "2024-05-06 13:37:13",
    },
    {
        "src": "/media4/源文件/",
        "dest": "/media4/电视剧/欧美剧/寻宝侦探 (2024)",
        "type": "电视剧",
        "category": "欧美剧",
        "tmdbid": 211288,
        "year": "2024",
        "date": "2024-05-06 13:37:13",
    },
    {
        "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
        "dest": "/media4/电视剧/欧美剧/寻宝侦探 (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
        "type": "电视剧",
        "category": "欧美剧",
        "tmdbid": 211288,
        "year": "2024",
        "date": "2024-05-06 13:37:13",
    },
    {
        "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
        "dest": "/media4/电视剧/欧美剧/AAAA (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
        "type": "电视剧",
        "category": "欧美剧",
        "tmdbid": 211288,
        "year": "2024",
        "date": "2024-05-06 13:37:13",
    },
    {
        "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
        "dest": "/media4/电视剧/欧美剧/CCCC (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
        "type": "电视剧",
        "category": "欧美剧",
        "tmdbid": 211288,
        "year": "2024",
        "date": "2024-05-06 13:37:13",
    },
    {
        "src": "/media4/源文件/电视剧/Tracker.2024.S01E11.1080p.WEB.h264-ETHEL.mkv",
        "dest": "/media4/电视剧/台陸劇/寻宝侦探 (2024)/Season 2/寻宝侦探 - S02E11 - 第 11 集.mkv",
        "type": "电视剧",
        "category": "欧美剧",
        "tmdbid": 211288,
        "year": "2024",
        "date": "2024-05-06 13:37:13",
    },
]
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
        if i != j and is_subpath(folderpath_to_process[j], folderpath_to_process[i]):
            folderpath_to_process.pop(j)
            break

print(folderpath_to_process)