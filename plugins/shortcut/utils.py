
from typing import Dict
from plugins.shortcut.config import *

def convert_bytes_to_human_readable(bytes_size, is_speed=False, add_unit=True, to_MB=False):
    """
    Convert bytes to human readable format.
    """
    if to_MB:
        bytes_size /= 1024.0 * 1024.0
        if is_speed:
            if add_unit:
                return "{:.2f} MB/s".format(bytes_size)
            else:
                return "{:.2f}".format(bytes_size)
        else:
            if add_unit:
                return "{:.2f} MB".format(bytes_size)
            else:
                return "{:.2f}".format(bytes_size)
    else:
        if is_speed:
            suffixes = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s']
        else:
            suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        while bytes_size > 1024 and suffix_index < len(suffixes) - 1:
            bytes_size /= 1024.0
            suffix_index += 1
        if add_unit:
            return "{:.2f} {}".format(bytes_size, suffixes[suffix_index])
        else:
            return "{:.2f}".format(bytes_size)
        
def check_error_within_range(value1, value2, error_range):
    # 計算誤差百分比
    error_percentage = abs((value1 - value2) / value1) * 100
    
    # 檢查誤差是否在範圍內
    return error_percentage <= error_range

def get_season_episode(
    begin_season: int,
    end_season: int = None,
    begin_episode: int = None,
    end_episode: int = None,
) -> str:
    if end_season is None:
        if begin_episode is None:
            return f"S{begin_season:02d}"
        elif end_episode is None:
            return f"S{begin_season:02d} E{begin_episode:02d}"
        else:
            return f"S{begin_season:02d} E{begin_episode:02d}-E{end_episode:02d}"
    else:
        return f"S{begin_season:02d}-S{end_season:02d}"

def get_site_score(site_name: str) -> int:
    return SITE_SCORES.get(site_name, SITE_SCORES["DEFAULT"])


def get_reource_team_score(resource_team: str) -> int:
    return RESOURCE_TEAM_SCORES.get(
        resource_team.lower(), RESOURCE_TEAM_SCORES["default"]
    )
    
def calculate_cp(title_info: Dict, important_const: float) -> float:
    cost = title_info["size"] / important_const
    # 循环匹配条件并应用系数
    for size_limit, coefficient in SIZE_COEFFICIENT_LIST:
        if title_info["size"] > size_limit:
            cost *= coefficient
            break  # 找到第一个满足条件的就停止循环

    performance = sum(get_site_score(site_name) for site_name in title_info["sites"])
    if title_info["resource_team"] is not None:
        resource_team_score = get_reource_team_score(title_info["resource_team"])
    else:
        resource_team_score = 1
    performance *= resource_team_score
    if "中字" in title_info["labels"]:
        if title_info["category"] not in CATRGORY_CHINESE:
            performance *= 100
        else:
            performance *= 5
    if "原盘" in title_info["description"]:
        performance /= 1000
    return round(performance * 10 / cost, 2)