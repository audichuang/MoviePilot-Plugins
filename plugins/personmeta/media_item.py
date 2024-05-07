from themoviedb import TMDb
TMDB_API_KEY = "db55323b8d3e4154498498a75642b381"

class MediaItem():
    """
    基类,表示电影或电视剧的基本信息。
    """

    def __init__(self, language: str = 'zh-TW'):
        self._tmdb = self._tmdb_init(language)
        self._tmdb_cn = self._tmdb_init('zh-CN')
        self._tmdb_en = self._tmdb_init('en-US')

    def _tmdb_init(self, language: str) -> TMDb:
        """
        初始化 TMDb 客户端实例。

        Args:
            language (str): 设置语言。

        Returns:
            TMDb: TMDb 客户端实例。

        Raises:
            ValueError: 如果 TMDB_API_KEY 未找到。
        """
        if not TMDB_API_KEY:
            raise ValueError("TMDB_API_KEY not found in configuration file")
        return TMDb(key=TMDB_API_KEY, language=language)