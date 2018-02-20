from __future__ import print_function
from ctypes import CDLL
import os
import sys


def get_steam_api():
    steam_api = CDLL('./libsteam_api.dylib')

    return steam_api


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Wrong number of arguments")
        sys.exit()

    str_app_id = sys.argv[1]

    os.environ["SteamAppId"] = str_app_id
    try:
        get_steam_api().SteamAPI_Init()
    except:
        print("Couldn't initialize Steam API")
        sys.exit()
