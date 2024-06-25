from .emby_user import EmbyUser
from app.schemas.types import MediaType
from app.log import logger


class EmbyItems(EmbyUser):
    def get_url_by_params(self, url: str, params):
        """
        根據url和參數獲取請求的url

        Args:
            url (str): 請求的url
            params (Dict[str, str]): 請求的參數

        Returns:
            str: 根據url和參數獲取的請求的url
        """
        # 組合url
        url = url + "?"
        for key, value in params.items():
            url = url + key + "=" + str(value) + "&"
        url = url[:-1]
        return url

    def get_type_items(self, media_type: MediaType = MediaType.TV):
        """
        獲取所有電影的信息列表。

        Returns:
            Items
        """
        basic_url = f"[HOST]/emby/Items"
        params = {
            "SortBy": "SortName",
            "SortOrder": "Ascending",
            "IncludeItemTypes": "Movie" if media_type == MediaType.MOVIE else "Series",
            "Recursive": "true",
            "Fields": "Path,ProviderIds",
            "api_key": "[APIKEY]",
        }
        response = self.get_data(self.get_url_by_params(basic_url, params))
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()["Items"]
        else:
            return None

    def get_item_info_by_tmdbid(
        self, tmdbid: int, media_type: MediaType = MediaType.TV
    ):
        """
        根據tmdb_id獲取媒體項目的信息。

        Args:
            tmdbid (int): tmdb_id。
            media_type (str, optional): 媒體類型,可以是'tv'或'movie'。默認為'tv'。

        Returns:
            Optional[Dict[str, str]]: 如果找到項目,返回包含id、名稱、年份、tmdb_id和路徑的字典;否則返回None。
        """
        result = self.get_type_items(media_type)
        if result is not None:
            for item in result:
                if str(item["ProviderIds"].get("Tmdb", "")) == str(tmdbid):
                    return item
        return None

    def get_tv_season_info_by_item_id(self, item_id: int):
        """
        根據項目id獲取電視劇季節的信息。

        Args:
            item_id (int): 項目id。

        Returns:
            Optional[Dict[str, str]]: 如果找到項目,返回包含id、名稱、年份、tmdb_id和路徑的字典;否則返回None。
        """
        # 構建 URL 和參數
        basic_url = f"[HOST]/emby/Shows/{item_id}/Seasons"
        params = {
            "api_key": "[APIKEY]",
            "Fields": "BasicSyncInfo,CanDelete,PrimaryImageAspectRatio,Overview,IndexNumber",
        }
        response = self.get_data(self.get_url_by_params(basic_url, params))
        print(response.url)
        print(response.status_code)

        # 處理響應
        if 200 <= response.status_code < 300:
            result = response.json()
            return result.get("Items", None)
        return None

    def get_tv_season_info_by_tmdbid(self, tmdbid: int, season_number: int):
        """
        根據tmdb_id和季節編號獲取電視劇季節的信息。

        Args:
            tmdbid (int): tmdb_id。
            season_number (int): 季節編號。

        Returns:
            Optional[Dict[str, str]]: 如果找到項目,返回包含id、名稱、年份、tmdb_id和路徑的字典;否則返回None。
        """
        item_info = self.get_item_info_by_tmdbid(tmdbid, media_type=MediaType.TV)
        if item_info is None:
            return None
        id = item_info.get("Id", None)
        if id is None:
            return None
        season_infos = self.get_tv_season_info_by_item_id(id)
        if season_infos is None:
            return None
        for season_info in season_infos:
            if int(season_info["IndexNumber"]) == season_number:
                return season_info
        return None

    def get_tv_episode_info_by_season_id(self, season_id: int):
        """
        根據季節id獲取電視劇季節的所有集數信息

        Args:
            season_id (int): 季節id

        Returns:
            Optional[Dict[str, str]]: 如果找到項目,返回包含Id、Name、Overview、IndexNumber和路徑的字典;否則返回None。
        """
        # 構建 URL 和參數
        basic_url = f"[HOST]/emby/Users/[USER]/Items"
        params = {
            "Fields": "BasicSyncInfo,CanDelete,PrimaryImageAspectRatio,Overview,PremiereDate,ProductionYear,RunTimeTicks,SpecialEpisodeNumbers,IndexNumber",
            "isFolder": "false",
            "ParentId": season_id,
            "api_key": "[APIKEY]",
        }
        response = self.get_data(self.get_url_by_params(basic_url, params))
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()["Items"]
        else:
            return None

    def get_tv_episode_info_by_tmdbid(self, tmdbid: int, season_number: int = 1):
        """
        根據tmdb_id和季節編號獲取電視劇季節的所有集數信息

        Args:
            tmdbid (int): tmdb_id。
            season_number (int): 季節編號。

        Returns:
            Optional[Dict[str, str]]: 如果找到項目,返回包含id、名稱、年份、tmdb_id和路徑的字典;否則返回None。
        """
        season_info = self.get_tv_season_info_by_tmdbid(tmdbid, season_number)
        if season_info is None:
            return None
        season_id = season_info["Id"]
        episode_info = self.get_tv_episode_info_by_season_id(season_id)
        if episode_info is None:
            return None
        return episode_info

    def is_episode_exist(self, tmdbid: int, season_number: int, episode_number: int):
        """
        根據tmdb_id、季節編號和集數獲取電視劇集數是否存在

        Args:
            tmdbid (int): tmdb_id。
            season_number (int): 季節編號。
            episode_number (int): 集數。

        Returns:
            bool: 如果集數存在返回True,否則返回False。
        """
        episode_info = self.get_tv_episode_info_by_tmdbid(tmdbid, season_number)
        if episode_info is None:
            return False
        for item in episode_info:
            if int(item["IndexNumber"]) == episode_number:
                return True
        return False

    def get_tmdbid_by_itemid(self, itemid: int):
        """
        根據Emby項目id獲取電視劇的tmdb_id

        Args:
            item_id (int): Emby項目id。

        Returns:
            int: 如果找到項目,返回tmdb_id;否則返回None。
        """
        basic_url = f"[HOST]/emby/Users/[USER]/Items/{itemid}"
        params = {
            "api_key": "[APIKEY]",
        }
        response = self.get_data(self.get_url_by_params(basic_url, params))
        if 200 <= response.status_code < 300:
            result = response.json()
            return result.get("ProviderIds", {}).get("Tmdb", None)
        else:
            logger.error(
                f"tv_itemid_to_tmdbid 請求失敗, status_code: {response.status_code}, error message: {response.text}"
            )
        return None


if __name__ == "__main__":
    emby = EmbyItems()
    season_id = 180949
    # episode_info = emby.get_tv_episode_info_by_season_id(season_id)
    # print(episode_info)
    episode_info = emby.get_tv_episode_info_by_tmdbid(234061, 1)
    print(episode_info)
    print(emby.is_episode_exist(234061, 1, 8))
    # print(emby.get_type_items(MediaType.MOVIE))
    # print(emby.get_item_info_by_tmdbid(974635, MediaType.MOVIE))
    # print(emby.get_tv_season_info_by_item_id(189657))
    # print(emby.get_tv_season_info_by_tmdbid(94997, 1))
