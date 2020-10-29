# -*- coding: utf-8 -*-
# __author__ = 'xuting'
import logging
import os


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


@singleton
class Wlog(object):
    def __init__(self, task=None):
        log_level = {'debug': logging.DEBUG,
                     'info': logging.INFO,
                     'warning': logging.WARNING,
                     'error': logging.ERROR,
                     'critical': logging.CRITICAL}
        self.format = "%(asctime)s  %(name)s  %(levelname)s : %(message)s"
        self.formatter = logging.Formatter(self.format, "%Y-%m-%d %H:%M:%S")
        self.level = log_level["debug"]
        self.stream_on = True
        if task:
            self.stream_on = task.stream_on
            self.log_path = os.path.join(task.outdir, "log.txt")
            self.file_handler = logging.FileHandler(self.log_path)
            self.file_handler.setLevel(self.level)
            self.file_handler.setFormatter(self.formatter)
            self.task = task
        if self.stream_on:
            self.stream_handler = logging.StreamHandler()
            self.stream_handler.setLevel(self.level)
            self.stream_handler.setFormatter(self.formatter)

    def get_logger(self, name=""):
        logger = logging.getLogger(name)
        logger.propagate = 0
        self._add_handler(logger)
        return logger

    def _add_handler(self, logger):
        logger.setLevel(self.level)
        if self.task:
            logger.addHandler(self.file_handler)
        if self.stream_on:
            logger.addHandler(self.stream_handler)
