import requests


headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NTZhNDFlODE2NTkxMzNjM2M5OTJjZGFiMzZkYjMyMSIsInN1YiI6IjY1ODViMWQ2NzFmMDk1NTdjNTIzZjdjMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Yafqg4nwY-i3mdhinliUOsS9MIKBGeCg2oEIG7y4wuk",
}


def _get_person_details(person_id, language="zh-TW"):
    url = f"https://api.themoviedb.org/3/person/{person_id}?language={language}"

    response = requests.get(url, headers=headers)
    return response.json()


def _get_movie_details(movie_id, language="zh-TW"):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language={language}"

    response = requests.get(url, headers=headers)
    return response.json()


def _get_tv_details(tv_id, language="zh-TW"):
    url = f"https://api.themoviedb.org/3/tv/{tv_id}?language={language}"

    response = requests.get(url, headers=headers)
    return response.json()


def _get_tv_season_details(tv_id, season_number, language="zh-TW"):
    url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}?language={language}"

    response = requests.get(url, headers=headers)
    return response.json()


def _get_tv_episode_details(tv_id, season_number, episode_number, language="zh-TW"):
    url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}/episode/{episode_number}?language={language}"

    response = requests.get(url, headers=headers)
    return response.json()


if __name__ == "__main__":
    tmdb_id = 1421
    result = _get_movie_details(850888)
    print(result)
    # result = _get_tv_details(tmdb_id)
    # print(result)
    # result = _get_tv_season_details(tmdb_id, 11)
    # print(result)
    # result = _get_tv_episode_details(tmdb_id, 11,2)
    # print(result)
