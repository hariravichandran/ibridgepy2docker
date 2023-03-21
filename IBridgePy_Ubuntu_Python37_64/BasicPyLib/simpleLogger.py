# -*- coding: utf-8 -*-
"""
Created on Thu Dec 25 19:01:54 2014

@author: IBridgePy
"""
import os
import datetime
import pytz

from BasicPyLib.retrying import retry

Level = {
    'NOTSET': 0,  # show more info
    'DEBUG': 10,
    'INFO': 20,
    'ERROR': 30}  # show less info


class SimpleLogger(object):
    """
    This is special because ALL messages are written to file.
    """
    def __init__(self, filename, logLevel, folderPath='default', addTime=True, logInMemory=False, verbose=True):
        """ determine US Eastern time zone depending on EST or EDT """
        if datetime.datetime.now(pytz.timezone('US/Eastern')).tzname() == 'EDT':
            self.USeasternTimeZone = pytz.timezone('Etc/GMT+4')
        elif datetime.datetime.now(pytz.timezone('US/Eastern')).tzname() == 'EST':
            self.USeasternTimeZone = pytz.timezone('Etc/GMT+5')
        else:
            self.USeasternTimeZone = None
        self.addTime = addTime  # True: add local time str in front of the records
        self.filename = filename  # User defined fileName
        self._logLevel = Level[logLevel]  #
        self._logInMemory = logInMemory  # When backtesting, only write messages to memory to save time of opening and closing log every time.
        self._allLogMessagesList = []  # all log messages will be written here and dump to file when backtesting is done. List.append will be faster than str concation.
        self._verbose = verbose
        if folderPath == 'default':
            self.folderPath = os.path.join(os.getcwd(), 'Log')
        else:
            self.folderPath = folderPath
        if not os.path.isdir(self.folderPath):
            os.makedirs(self.folderPath)
            print(__name__ + '::__init__: WARNING, create a folder of "Log" at %s' % (self.folderPath,))

    def __str__(self):
        return '{fileName=%s}' % (self.filename,)

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def _write_to_log(self, msg, logLevel, verbose):
        if self._logLevel <= logLevel:
            if verbose:
                print(msg)
        if self._logInMemory:
            self._allLogMessagesList.append(msg)
        else:
            with open(os.path.join(self.folderPath, self.filename), 'a') as fp:
                if self._logLevel <= logLevel:
                    if self.addTime:
                        currentTime = datetime.datetime.now(tz=self.USeasternTimeZone)
                        fp.write(str(currentTime) + ": " + msg + '\n')
                    else:
                        fp.write(msg + '\n')
                else:
                    fp.write(' ')

    def write_all_messages_to_file(self):
        if self._allLogMessagesList:
            with open(os.path.join(self.folderPath, self.filename), 'a') as fp:
                allLog = '\n'.join(self._allLogMessagesList)
                fp.write(allLog)

    def notset(self, msg, verbose=True):
        self._write_to_log(msg, Level['NOTSET'], verbose)

    def debug(self, msg, verbose=True):
        self._write_to_log(msg, Level['DEBUG'], verbose)

    def info(self, msg, verbose=True):
        self._write_to_log(msg, Level['INFO'], verbose)

    def error(self, msg, verbose=True):
        self._write_to_log(msg, Level['ERROR'], verbose)

    def record(self, *arg, **kwrs):
        msg = ''
        for ct in arg:
            msg += str(ct) + ' '
        for ct in kwrs:
            msg += str(kwrs[ct]) + ' '
        self._write_to_log(msg, Level['NOTSET'], True)
