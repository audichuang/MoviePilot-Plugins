import os
import re
import xml.etree.ElementTree as ET
from app.log import logger


class NfoFileManager:
    """
    管理 NFO 文件的类。
    """

    def find_nfo_files(target_directory: str):
        """
        在目标目录中查找所有的 .nfo 文件,并返回完整文件路径列表。

        Args:
            target_directory (str): 目标目录的路径。

        Returns:
            list[str]: 包含 .nfo 文件的完整文件路径列表。
        """
        nfo_files = []
        for root, _, files in os.walk(target_directory):
            for file in files:
                if file.endswith(".nfo"):
                    nfo_file_path = os.path.join(root, file)
                    nfo_files.append(nfo_file_path)
        return nfo_files

    def has_tag(nfo_file_path: str, tag: str = "<tvshow>") -> bool:
        """
        检查 NFO 文件是否包含指定的标签。

        Args:
            nfo_file_path (str): NFO 文件的路径。
            tag (str, optional): 要检查的标签。默认为 "<tvshow>"。

        Returns:
            bool: 如果文件包含指定标签,返回 True;否则返回 False。
        """
        with open(nfo_file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(tag):
                    return True
        return False

    def read_nfo_file(file_path: str):
        """
        读取 NFO 文件中的标签及其内容。

        Args:
            file_path (str): NFO 文件的路径。

        Returns:
            Dict[str, str]: 包含标签及其内容的字典。
        """
        try:
            NfoFileManager.process_nfo_empty_tags(file_path)
            tree = ET.parse(file_path)
            logger.info(f"讀取 NFO 文件 {file_path}")
            return tree.getroot()
        except Exception as e:
            logger.error(f"讀取 NFO 文件 {file_path} 失敗: {e}")
        

    def get_property(root):
        """
        读取 NFO 文件中的标签及其内容。

        Args:
            root (Element): NFO 文件的根元素。

        Returns:
            Dict[str, str]: 包含标签及其内容的字典。
        """
        try:
            properties = {}
            for child in root:
                tag = child.tag
                text = child.text.strip() if child.text else ""
                properties[tag] = text
            return properties
        except Exception as e:
            logger.error(f"獲取標籤內容 {root} 失敗: {e}")

    def season_nfo_find_tvshow_nfo(nfo_file_path: str):
        """
        根据给定的 seaseon.nfo 文件路径,查找对应的 tvshow.nfo 文件。

        Args:
            nfo_file_path (str): .nfo 文件的完整路径。

        Returns:
            Optional[str]: tvshow.nfo 文件的完整路径,如果找不到则返回 None。
        """
        try:
            logger.info(f"查找 {nfo_file_path}  的tvshow.nfo 文件")
            directory = os.path.dirname(nfo_file_path)
            last_sep_index = directory.rfind(os.path.sep)
            tvshow_nfo_path = os.path.join(directory[:last_sep_index], "tvshow.nfo")
            if os.path.exists(tvshow_nfo_path):
                logger.info(f"找到 {nfo_file_path}  的tvshow.nfo 文件: {tvshow_nfo_path}")
                return tvshow_nfo_path
            return None
        except Exception as e:
            logger.error(f"查找 {nfo_file_path}  的tvshow.nfo 文件失败: {e}")
            return None

    def process_nfo_empty_tags(nfo_file_path):
        """
        处理 NFO 文件, 修复其中的空标签<tag />，并将其转换为<tag></tag>。
        """

        def restore_empty_tags(xml_string):
            pattern = r"<(\w+) />"
            return re.sub(pattern, r"<\1></\1>", xml_string)

        with open(nfo_file_path, "r", encoding="utf-8") as f:
            original_xml = f.read()
        restored_xml = restore_empty_tags(original_xml)
        with open(nfo_file_path, "w", encoding="utf-8") as f:
            f.write(restored_xml)

    def modify_nfo_file(nfo_file_path: str, modifications) -> bool:
        """
        修改 NFO 文件中指定标签的内容。
        Args:
            nfo_file_path (str): NFO 文件的路径。
            modifications (Dict[str, str]): 包含要修改的标签及其对应的新值的字典。
        Returns:
            bool: 如果修改成功,返回 True;否则返回 False。
        """
        try:
            with open(nfo_file_path, "r", encoding="utf-8") as f:
                xml_data = f.read()
                xml_declaration = xml_data.split('\n')[0] + '\n'    # 保存 xml 声明

            root = ET.fromstring(xml_data)
            for tag_name, new_text in modifications.items():
                element = root.find(tag_name)
                if element is not None:
                    if new_text != "":
                        element.text = new_text
                        
            modified_xml_string = ET.tostring(root, encoding='utf-8', method='xml')
            modified_xml_string = re.sub(b'<(plot|outline) />(?!</\\1>)', b'<\\1></\\1>', modified_xml_string)       
            with open(nfo_file_path, 'w', encoding='utf-8') as f:
                f.write(xml_declaration)
                f.write(modified_xml_string.decode('utf-8'))

            NfoFileManager.process_nfo_empty_tags(nfo_file_path)

            with open(nfo_file_path, "r", encoding="utf-8") as f:
                modified_xml_data = f.read()
                modified_root = ET.fromstring(modified_xml_data)

            for tag_name, expected_text in modifications.items():
                element = modified_root.find(tag_name)
                if expected_text != "":
                    if element is None or element.text != expected_text:
                        logger.error(
                            f"修改标签 '{tag_name}' 失败, 预期值为 '{expected_text}', 实际值为 '{element.text if element is not None else 'None'}'"
                        )
                        return False
                else:
                    continue
            logger.info(f"成功修改文件 {nfo_file_path}")
            return True
        except Exception as e:
            logger.info(f"修改文件 {nfo_file_path} 失敗: {e}")
            return False


# if __name__ == "__main__":
#     nfo_file_path = "/home/audichuang/media_4/測試/电影/57秒 (2023) - 1080p.nfo"
#     a = NfoFileManager.read_nfo_file(nfo_file_path)
#     b = NfoFileManager.get_property(a)
#     # print(b)

#     from media_items.movie import Movie
#     from media_items.tv_show import TvShow
#     import zhconv
#     # dict = TvShow.get_tvshow_nfo_update_dict(250427, zhconv)
#     # print(dict)
#     # NfoFileManager.modify_nfo_file(nfo_file_path, dict)
#     dict = Movie.get_movie_nfo_update_dict(937249, zhconv)
#     NfoFileManager.modify_nfo_file(nfo_file_path, dict)
    # tree = ET.parse("/home/audichuang/media_4/測試/电视剧/七人的复活 (2024)/Season 1/七人的复活 - S01E01 - 第 1 集.nfo")
    # root = tree.getroot()
    # properties = {}
    # for child in root:
    #     tag = child.tag
    #     text = child.text.strip() if child.text else ""
    #     properties[tag] = text
    # print(properties)
