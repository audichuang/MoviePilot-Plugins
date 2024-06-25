from app.modules.emby import Emby
from app.log import logger


class EmbyUser(Emby):
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

    def get_all_users_info(self):
        basic_url = f"[HOST]/emby/Users/Query"
        params = {
            "api_key": "[APIKEY]",
        }

        response = self.get_data(self.get_url_by_params(basic_url, params))

        if response.status_code >= 200 and response.status_code < 300:
            return response.json()["Items"]
        logger.error(f"獲取所有使用者信息失敗:{response.status_code}")
        return None

    def get_all_users_id(self):
        users_info = self.get_all_users_info()
        user_dict = {}
        if users_info is not None:
            for user in users_info:
                user_dict[user["Name"]] = user["Id"]
            return user_dict
        else:
            logger.error("獲取所有使用者id失敗:")
            return None

    def get_user_id_by_name(self, user_name: str):
        users_info = self.get_all_users_info()
        if users_info is not None:
            for user in users_info:
                if user["Name"] == user_name:
                    return user["Id"]
        return None

    def get_user_favorite_tv(self, user_id: str):
        basic_url = f"[HOST]/emby/Users/{user_id}/Items"
        params = {
            "api_key": "[APIKEY]",
            "Filters": "IsFavorite",
            "Recursive": "true",
            "IncludeItemTypes": "Series",
        }

        response = self.get_data(self.get_url_by_params(basic_url, params))
        if response.status_code >= 200 and response.status_code < 300:
            result = response.json()["Items"]
            itemid_list = []
            for item in result:
                itemid_list.append(item["Id"])
            return itemid_list
        return None

    def get_all_user_favorite_dict(self):
        logger.info("獲取全面使用者id")
        user_dict = self.get_all_users_id()
        logger.info("獲取全面使用者id完成:{user_dict}")
        logger.info("獲取全面使用者收藏的電視劇")
        favorite_dict = {}
        for user_name, user_id in user_dict.items():
            favorite_dict[user_name] = self.get_user_favorite_tv(user_id)
        logger.info("獲取全面使用者收藏的電視劇完成:{favorite_dict}")
        return favorite_dict


if __name__ == "__main__":
    embyuser = EmbyUser()
    print(embyuser.get_all_user_favorite_dict())
