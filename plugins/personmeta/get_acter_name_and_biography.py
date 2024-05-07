import requests
import zhconv


headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NTZhNDFlODE2NTkxMzNjM2M5OTJjZGFiMzZkYjMyMSIsInN1YiI6IjY1ODViMWQ2NzFmMDk1NTdjNTIzZjdjMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Yafqg4nwY-i3mdhinliUOsS9MIKBGeCg2oEIG7y4wuk"
    }

def _get_person_details(person_id, language='zh-TW'):
    url = f"https://api.themoviedb.org/3/person/{person_id}?language={language}"

    response = requests.get(url, headers=headers)
    return response.json()
    
def _get_actor_traditional_chinese_name(tmdb_id):
    response = requests.get(f"https://actor.audiweb.uk/actors/{int(tmdb_id)}")
    if response.status_code == 200:
        result = response.json()["name"]
        if result is None:
            return ""
        elif result != "error":
            return str(result)
        else:
            return ""
    return ""
    
def _get_biography(tmdb_id):
    tmdb_languages = ["zh-TW", "zh-CN"]
    for tmdb_language in tmdb_languages:
        details = _get_person_details(tmdb_id, tmdb_language)
        print(details)
        if details and details["biography"]:
            if tmdb_language == "zh-CN":
                return zhconv.convert(details["biography"], "zh-tw")
            else:
                return details["biography"]
    return None
    
# zhconv.convert(name, "zh-tw")
# if __name__ == "__main__":
#     print(_get_actor_traditional_chinese_name(2808137))
#     mediaItem = MediaItem()
    # print(_get_biography(500))