# -*- coding: utf-8 -*-
import importer
import argparse
import glob
import os
import logging
import time
import configobj
import pysftp

config = configobj.ConfigObj('config.ini')


def downloadDeltas():
    """
    simple file download 
    """
    with pysftp.Connection(config['sftp']['host'], username=config['sftp']['user'], password=config['sftp']['pass']) as sftp:
        files = list(filter(lambda x: x.endswith('txt') or x.endswith('TXT'), sftp.listdir()))
        for file in files:
            sftp.get(file)

    return files


def run(all=False, download=True):
    """
    Main runner method

    :param bool all: process all files in folder or not
    """

    now = time.strftime('%Y%m%d')

    logging.basicConfig(level=logging.DEBUG,
                        format='[ %(levelname)s ] %(asctime)s - %(name)s - %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='log/abr%s.txt' % now)

    os.chdir("data/delta")
    os.makedirs('../imported/', exist_ok=True)
    if download:
        process = downloadDeltas()

    if all or download is False:
        process = glob.glob("*.txt")

    for file in process:
        print('importing: %s' % file)
        try:
            importer.FileParseAbr(file)
            os.makedirs('../imported/%s' % now, exist_ok=True)
        except Exception as e:
            logging.error(e)
        finally:
            os.rename(file, '../imported/%s/%s' % (now, file))
    exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ABR delta importing")
    parser.add_argument("-a", "--all",
                        dest="all",
                        default=False,
                        action='store_true',
                        help="Run parser for all files in data folder")
    parser.add_argument("-r", "--run_only",
                        dest="run",
                        default=True,
                        action='store_false',
                        help="Dont download new files from sftp server, overrides the -a option")
    args = parser.parse_args()

    run(all=args.all, download=args.run)
