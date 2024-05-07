import requests
from media_item import MediaItem
import zhconv

mediaItem = MediaItem()

def _get_actor_traditional_chinese_name(tmdb_id):
    response = requests.get(f"https://actor.audiweb.uk/actors/{tmdb_id}")
    if response.status_code == 200:
        result = response.json()["name"]
        if result != "error":
            return result
    else:
        return None
def _get_biography(tmdb_id):
    tmdb_instances = [mediaItem._tmdb, mediaItem._tmdb_cn]
    for tmdb_instance in tmdb_instances:
        details = tmdb_instance.person(tmdb_id).details()
        if details and details.biography:
            if tmdb_instance == mediaItem._tmdb_cn:
                return zhconv.convert(details.biography, "zh-tw")
            else:
                return details.biography
    return None
    
# zhconv.convert(name, "zh-tw")
# if __name__ == "__main__":
#     print(_get_actor_traditional_chinese_name(2644771))
#     mediaItem = MediaItem()
#     details_tw = mediaItem._tmdb.person(4690).details()
#     details_cn = mediaItem._tmdb_cn.person(4690).details()
#     print(details_tw.biography)
#     print(details_cn.biography)
#     print(_get_biography(1196101))