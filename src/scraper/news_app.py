import os
import logging
from typing import List
from datetime import datetime, date
from environs import Env
from .input import NewsFeedInputHandler
from .output import JsonObjectOutputHandler
from .news_paper import NewsPaper
from .news_feed import NewsFeed
from .article_error_log import ArticleErrorLog
from .mongo_connection_settings import MongoConnectionSettings
from .mongo_connection import MongoConnection
from .datetime_provider import DateTimeProvider


class NewsApp:
    DEFAULT_LOG_LEVEL = 'INFO'
    ERROR_LOG_FILE = 'error_logs.txt'

    def __init__(self):
        self.error_logs: List[ArticleErrorLog] = []

    # pylint: disable=too-many-locals
    def accept(self):
        self.apply_logging_level()
        self.load_env_vars()

        start_time = datetime.now()
        logging.info("Start Time: %s", start_time)
        logging.info('Started scraping from all sources.')

        try:
            news_feed_input_handler = NewsFeedInputHandler()
            args_map = news_feed_input_handler.fetch_arguments()

            mongo_connection_settings = MongoConnectionSettings()
            mongo_connection = MongoConnection(mongo_connection_settings)

            root_dir = args_map['root_dir']
            source_list = news_feed_input_handler.get_all_sources()
            json_object_output_handler = JsonObjectOutputHandler(output_root_dir=root_dir, mongo_connection=mongo_connection)

            datetime_provider = DateTimeProvider()
            papers = self.create_newspaper_objects(source_list, json_object_output_handler, datetime_provider)

            news_feed = NewsFeed(papers, root_dir)

            # Start processing the articles
            news_feed.build()
            self.generate_error_logs(root_dir)

            logging.info('Scraping completed successfully.')
            logging.info("Errored out articles count: %d", len(self.error_logs))

            end_time = datetime.now()
            logging.info("End Time: %s", end_time)

            elapsed = (end_time - start_time).seconds
            logging.info("Total elapsed time: %s", elapsed)

        # pylint: disable=broad-except
        except Exception as exception:
            logging.exception("Error occured during scraping ", exc_info=exception)

            end_time = datetime.now()
            elapsed = (end_time - start_time).seconds
            logging.info("Total elapsed time: %s", elapsed)

    @classmethod
    def apply_logging_level(cls):
        logger = logging.getLogger()
        logger.setLevel(cls.get_logging_level())

    @classmethod
    def get_logging_level(cls):
        log_level_env = os.environ.get('LOGLEVEL')

        if log_level_env is None:
            return cls.DEFAULT_LOG_LEVEL

        return log_level_env

    @staticmethod
    def load_env_vars():
        env = Env()
        # Read .env into os.environ
        env.read_env()

    def create_newspaper_objects(self, source_list, json_object_output_handler, datetime_provider):
        papers: List[NewsPaper] = []
        for source in source_list:
            papers.append(NewsPaper(source, datetime_provider, json_object_output_handler, self.error_logs))

        return papers

    def generate_error_logs(self, output_root_dir):
        today = date.today()
        dir_suffix = today.strftime("%Y-%m-%d")
        error_log_file_path = output_root_dir + '/' + dir_suffix + '/' + self.ERROR_LOG_FILE

        with open(error_log_file_path, 'w') as file:
            for error_log in self.error_logs:
                file.write("{0}|{1}|{2}\n".format(error_log.url, error_log.source, error_log.error_message))