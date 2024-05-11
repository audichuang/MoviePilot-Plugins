from torrent_list_example import data
from typing import Dict, List
from plugins.shortcut.utils import convert_bytes_to_human_readable, check_error_within_range
from plugins.shortcut.config import *



def find_duplicate_titles(
    data: List[Dict], type: str = "movie", season_episode: str = "S01"
) -> Dict[str, Dict]:
    title_lists = {}
    for torrent in data:
        title = torrent["torrent_info"]["title"].strip()
        size = float(
            convert_bytes_to_human_readable(
                torrent["torrent_info"]["size"], add_unit=False, to_MB=True
            )
        )

        site_name = torrent["torrent_info"]["site_name"]
        seeders = torrent["torrent_info"]["seeders"]
        volume_factor = torrent["torrent_info"]["volume_factor"]
        torrent_season_episode = torrent["meta_info"]["season_episode"]
        description = torrent["torrent_info"]["description"]
        labels = torrent["torrent_info"]["labels"]
        if "中字" not in labels:
            for keyword in SUBSTITUTE_KEYWORD_LIST:
                if keyword in description:
                    labels.append("中字")
                    break
        category = torrent["media_info"]["category"]
        if torrent["meta_info"]["resource_team"] is None:
            resource_team = get_resource_team_from_title(title)
        else:
            resource_team = torrent["meta_info"]["resource_team"]
        # 預防朋友站的資源沒有標注FRDS
        if resource_team is None and site_name == "朋友":
            resource_team = "FRDS"
        resource_type = torrent["meta_info"]["resource_type"]
        video_encode = torrent["meta_info"]["video_encode"]

        resolution = torrent["meta_info"]["resource_pix"]
        edition = torrent["meta_info"]["edition"]

        if type == "tv" and season_episode != torrent_season_episode:
            continue
        for key, Value in title_lists.items():
            # 檢查兩者容量是否差不多
            if check_error_within_range(Value["size"], size, 0.3):
                # 檢查他們是否為相同來源 相同片源的種子
                if (
                    Value["edition"] == edition
                    and Value["resource_type"] == resource_type
                    and Value["video_encode"] == video_encode
                    and Value["resolution"] == resolution
                ):
                    # 判斷製作組
                    try:
                        same = has_common_element(
                            Value["resource_team"].split("@"), resource_team.split("@")
                        )
                    except:
                        # 如果製作組不同，可能一個None不代表不一樣，檢查容量是否差不多
                        if Value["resource_team"] == resource_team:
                            same = True
                        elif (
                            Value["resource_team"] is not None
                            and resource_team is None
                            and check_error_within_range(Value["size"], size, 0.01)
                        ):
                            # 若原本有製作組，但現在沒有，則用原來的製作組找看看新的title是否有先關的字體
                            if Value["resource_team"].lower() in title.lower():
                                same = True
                            else:
                                same = False
                        elif (
                            Value["resource_team"] is None
                            and resource_team is not None
                            and check_error_within_range(Value["size"], size, 0.01)
                        ):
                            # 若原本沒有製作組，但現在有，則用新的製作組找看看原本的title是否有先關的字體
                            if resource_team.lower() in key.lower():
                                same = True
                            else:
                                same = False
                        else:
                            same = False
                    finally:
                        if same:
                            # 確認為相同種子 判斷是否已經存有站點
                            if site_name not in Value["sites"]:
                                Value["sites"].append(site_name)
                                Value["torrents"].append(torrent)
                                Value["torrent_dict"][site_name] = torrent
                            else:
                                for i, existing_torrent in enumerate(Value["torrents"]):
                                    if (
                                        existing_torrent["torrent_info"]["site_name"]
                                        == site_name
                                    ):
                                        if (
                                            seeders
                                            > existing_torrent["torrent_info"][
                                                "seeders"
                                            ]
                                        ):
                                            print(f"替代{site_name}")
                                            Value["torrents"][i] = torrent
                            break

        else:
            title_lists[title + " " + str(size) + " MB"] = {
                "resolution": resolution,
                "size": size,
                "sites": [site_name],
                "torrent_dict": {site_name: torrent},
                "torrents": [torrent],
                "category": category,
                "volume_factor": volume_factor,
                "labels": labels,
                "description": description,
                "edition": edition,
                "resource_type": resource_type,
                "video_encode": video_encode,
                "resource_team": resource_team,
            }

    return title_lists

if __name__ == "__main__":
    result = find_duplicate_titles(data, type="tv")
    print(result)