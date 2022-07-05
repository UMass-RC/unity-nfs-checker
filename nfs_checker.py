"""
Simon Leary
7/1/2022
Filesystem Responsiveness Checker

for each dir in dir_list, time how long it takes to `ls`
do this once every loop_wait_time_s seconds
if any of these times are greater than min_report_time_s, add a line to the report queue
if there's anything in the queue,
    and it's been more than max_email_frequency_min since the last email,
    and email is enabled in the config
send an email containing the report queue, and clear the queue.
"""
CONFIG_PREPEND = """
# nfs_checker_config.ini contains a cleartext password
#     should be excluded from source control!
#     should not be readable by any other user!
"""
import os
import time
import datetime
from threading import Thread
import logging
from logging.handlers import RotatingFileHandler
import smtplib
from email.message import EmailMessage
import configparser
import sys
import traceback
from typing import List

CONFIG = None
LOG = None

def multiline_str(*argv: str) -> str:
    return '\n'.join(argv)

def purge_element(_list: list, elem_to_purge) -> list:
    return [elem for elem in _list if elem != elem_to_purge]

def parse_multiline_config_list(string: str) -> list:
    """
    delete newlines, split by commas, strip each string, remove empty strings
    """
    return purge_element([state.strip() for state in string.replace('\n', '').split(',')], '')

def str_to_bool(string) -> bool:
    if string.lower() in ['true', '1', 't', 'y', 'yes']:
        return True
    if string.lower() in ['false', '0', 'f', 'n', 'no']:
        return False
    return None

def purge_str(_list: List[str], str_to_purge, case_sensitive=True) -> list:
    """
    purge a string from a list
    converts list elements to string and does logic with that
    strips both the list elements and str_to_purge before comparing
    """
    if case_sensitive:
        return [elem for elem in _list if str(elem).strip() != str_to_purge.strip()]
    else:
        return [elem for elem in _list if str(elem).lower().strip() != str_to_purge.lower().strip()]

def now_str(time_only=False):
    """
    if you want just the time, use 'time' as an argument.
    else, you get %Y-%m-%d_%H-%M-%S
    does not use colons because colons aren't allowed in filenames.
    """
    _format = '%Y-%m-%d_%H-%M-%S'
    if time_only:
        _format = '%I-%M-%S'
    return datetime.datetime.now().strftime(_format)

def make_daemon_thread(function, thread_name="anon_thread"):
    """
    does not join()
    """
    Thread(target=function, daemon=True, name=thread_name).start()

def init_logger(info_filename='nfs_checker.log', error_filename='nfs_checker_error.log',
                max_filesize_megabytes=1024, rollover_count=1, do_print=True,
                name='nfs_checker') -> logging.Logger:
    """
    creates up to 4 log files, each up to size max_filesize_megabytes
        info_filename
        info_filename.1 (backup)
        error_filename
        error_filename.1 (backup)
    """
    log = logging.getLogger(name)
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    if do_print:
        stream_handler = logging.StreamHandler()
        log.addHandler(stream_handler)

    file_handler_info = RotatingFileHandler(
        info_filename,
        mode='w',
        maxBytes=max_filesize_megabytes*1024*1024,
        backupCount=rollover_count)
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(logging.INFO)
    log.addHandler(file_handler_info)

    file_handler_error = RotatingFileHandler(
        error_filename,
        mode='w',
        maxBytes=max_filesize_megabytes*1024,
        backupCount=rollover_count)
    file_handler_error.setFormatter(log_formatter)
    file_handler_error.setLevel(logging.ERROR)
    log.addHandler(file_handler_error)

    log.setLevel(logging.INFO)

    # global exception handler write to log file
    def my_excepthook(exc_type, exc_value, exc_traceback):
        exc_lines = traceback.format_exception(exc_type, "", exc_traceback)
        exc_lines = [line.strip() for line in exc_lines]
        for line in exc_lines:
            LOG.error(line)
        LOG.error(exc_value)
        sys.exit()
    sys.excepthook = my_excepthook

    return log

def send_email(to: str, _from: str, subject: str, body: str, signature: str,
               hostname: str, port: int, user: str, password: str, is_ssl: bool) -> None:
    body = multiline_str(
        body,
        '',
        signature
    )
    LOG.error(multiline_str(
        "sending email:_______________________________________________________________",
        f"to: {to}",
        f"from: {_from}",
        f"subject: {subject}",
        "body:",
        body,
    ))
    msg = EmailMessage()
    msg.set_content(body)
    msg['To'] = to
    msg['From'] = _from
    msg['Subject'] = subject

    if is_ssl:
        smtp = smtplib.SMTP_SSL(hostname, port, timeout=5)
    else:
        smtp = smtplib.SMTP(hostname, port, timeout=5)
    smtp.login(user, password)
    smtp.send_message(msg)
    smtp.quit()

    LOG.info("email sent successfully!____________________________________________________")

def check_dir(_dir):
    before = datetime.datetime.now()
    os.listdir(_dir)
    after = datetime.datetime.now()
    duration_s = (after - before).total_seconds()
    return duration_s

def init_config():
    config = configparser.ConfigParser()
    if os.path.isfile('nfs_checker_config.ini'):
        config.read('nfs_checker_config.ini')
    else:
        # write default empty config file
        config['email'] = {
            "enabled" : "False",
            "to" : "",
            "from" : "",
            "signature" : "",
            "smtp_server" : "",
            "smtp_port" : "",
            "smtp_user" : "",
            "smtp_password" : "",
            "smtp_is_ssl" : "False",
            "max_email_frequency_min" : "30"
        }
        config['logger'] = {
            "info_filename" : "nfs_checker.log",
            "error_filename" : "nfs_checker_error.log",
            "max_filesize_megabytes" : "100",
            "rollover_count" : "1"
        }
        config['misc'] = {
            "dir_list" : "",
            "min_report_time_s" : "0.25",
            "loop_wait_time_s" : "10"
        }
        with open('nfs_checker_config.ini', 'w', encoding='utf-8') as config_file:
            config_file.write(CONFIG_PREPEND)
            config.write(config_file)
        os.chmod('nfs_checker_config.ini', 0o700)
    return config

if __name__=='__main__':
    CONFIG = init_config()
    LOG = init_logger(CONFIG['logger']['info_filename'], CONFIG['logger']['error_filename'],
        int(CONFIG['logger']['max_filesize_megabytes']), int(CONFIG['logger']['rollover_count']))
    LOG.info("hello, world!")

    time_last_sent_email_s = None
    email_report_queue = ''
    dir_list = parse_multiline_config_list(CONFIG['misc']['dir_list'])
    if len(purge_str(dir_list, '')) == 0:
        raise Exception("there are no directories for me to check!")
    while True:
        for _dir in dir_list:
            i_time_s = check_dir(_dir)
            report = f"{_dir}\t took {i_time_s}\t seconds to `ls`"
            if i_time_s > float(CONFIG['misc']['min_report_time_s']):
                LOG.error(report)
                email_report_queue = email_report_queue + now_str() + '\t' + report + '\n'
            else:
                LOG.info(report)

        do_email = False
        if email_report_queue.strip() != '':
            if time_last_sent_email_s is None:
                do_email = True
            else:
                time_since_last_sent_email_s = (datetime.datetime.now() - time_last_sent_email_s).total_seconds()
                if time_since_last_sent_email_s/60 > int(CONFIG['email']['max_email_frequency_min']):
                    do_email = True
        if do_email and str_to_bool(CONFIG['email']['enabled']):
            time_last_sent_email_s = datetime.datetime.now()
            send_email(
                CONFIG['email']['to'],
                CONFIG['email']['from'],
                'filesystems are slow!',
                email_report_queue,
                CONFIG['email']['signature'],
                CONFIG['email']['smtp_server'],
                int(CONFIG['email']['smtp_port']),
                CONFIG['email']['smtp_user'],
                CONFIG['email']['smtp_password'],
                str_to_bool(CONFIG['email']['smtp_is_ssl'])
            )
            email_report_queue = ''

        time.sleep(int(CONFIG['misc']['loop_wait_time_s']))
