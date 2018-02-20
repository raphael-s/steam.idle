from colorama import init, Fore
import bs4
import datetime
import json
import logging
import os
import re
import requests
import subprocess
import sys
import time


init()

os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))

logging.basicConfig(filename="idlemaster.log", filemode="w",
                    format="[ %(asctime)s ] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
console.setFormatter(logging.Formatter(
    "[%(asctime)s] %(message)s", "%m/%d/%Y %I:%M:%S"))
logging.getLogger('').addHandler(console)

logging.warning(Fore.GREEN + "WELCOME TO IDLE MASTER" + Fore.RESET)

DROP_DELAY = 2*60

try:
    authData = {}
    authData["sort"] = ""
    authData["hasPlayTime"] = "false"
    execfile("./settings.txt", authData)
    myProfileURL = "http://steamcommunity.com/profiles/" + \
        authData["steamLogin"][:17]
except:
    logging.warning(Fore.RED + "Error loading config file" + Fore.RESET)
    raw_input("Press Enter to continue...")
    sys.exit()

if not authData["sessionid"]:
    logging.warning(Fore.RED + "No sessionid set" + Fore.RESET)
    raw_input("Press Enter to continue...")
    sys.exit()

if not authData["steamLogin"]:
    logging.warning(Fore.RED + "No steamLogin set" + Fore.RESET)
    raw_input("Press Enter to continue...")
    sys.exit()


def generateCookies():
    global authData
    try:
        cookies = dict(
            sessionid=authData["sessionid"], steamLogin=authData["steamLogin"])
    except:
        logging.warning(Fore.RED + "Error setting cookies" + Fore.RESET)
        raw_input("Press Enter to continue...")
        sys.exit()

    return cookies


def idleOpen(appID):
    try:
        logging.warning("Starting game " +
                        getAppName(appID) + " to idle cards")
        global process_idle
        global idle_time

        idle_time = time.time()

        process_idle = subprocess.Popen(['python ./steam-idle.py %s' % appID], shell=True)
    except:
        logging.warning(
            Fore.RED + "Error launching steam-idle with game ID " + str(appID) + Fore.RESET)
        raw_input("Press Enter to continue...")
        sys.exit()


def idleClose(appID):
    try:
        logging.warning("Closing game " + getAppName(appID))
        process_idle.terminate()
        total_time = int(time.time() - idle_time)
        logging.warning(getAppName(appID) + " took " + Fore.GREEN +
                        str(datetime.timedelta(seconds=total_time)) + Fore.RESET + " to idle.")
    except:
        logging.warning(Fore.RED + "Error closing game. Exiting." + Fore.RESET)
        raw_input("Press Enter to continue...")
        sys.exit()


def chillOut(appID):
    logging.warning("Suspending operation for "+getAppName(appID))
    idleClose(appID)
    stillDown = True
    while stillDown:
        logging.warning("Sleeping for 2 minutes.")
        time.sleep(DROP_DELAY)
        try:
            rBadge = requests.get(
                myProfileURL+"/gamecards/" + str(appID) + "/", cookies=cookies)
            indBadgeData = bs4.BeautifulSoup(rBadge.text)
            badgeLeftString = indBadgeData.find_all(
                "span", {"class": "progress_info_bold"})[0].contents[0]
            if "card drops" in badgeLeftString:
                stillDown = False
        except:
            logging.warning("Still unable to find drop info.")
    # Resume operations.
    idleOpen(appID)


def getAppName(appID):
    try:
        api = requests.get(
            "http://store.steampowered.com/api/appdetails/?appids=" + str(appID) + "&filters=basic")
        api_data = json.loads(api.text)
        return Fore.CYAN + api_data[str(appID)]["data"]["name"].encode('ascii', 'ignore') + Fore.RESET
    except:
        return Fore.CYAN + "App "+str(appID) + Fore.RESET


def getPlainAppName(appid):
    try:
        api = requests.get(
            "http://store.steampowered.com/api/appdetails/?appids=" + str(appID) + "&filters=basic")
        api_data = json.loads(api.text)
        return api_data[str(appID)]["data"]["name"].encode('ascii', 'ignore')
    except:
        return "App "+str(appID)


logging.warning("Finding games that have card drops remaining")

try:
    cookies = generateCookies()
    r = requests.get(myProfileURL+"/badges/", cookies=cookies)
except:
    logging.warning(Fore.RED + "Error reading badge page" + Fore.RESET)
    raw_input("Press Enter to continue...")
    sys.exit()

try:
    badgesLeft = []
    badgePageData = bs4.BeautifulSoup(r.text, "html.parser")
    badgeSet = badgePageData.find_all("div", {"class": "badge_title_stats"})
except:
    logging.warning(Fore.RED + "Error finding drop info" + Fore.RESET)
    raw_input("Press Enter to continue...")
    sys.exit()

# For profiles with multiple pages
try:
    badgePages = int(badgePageData.find_all(
        "a", {"class": "pagelink"})[-1].text)
    if badgePages:
        logging.warning(str(badgePages) +
                        " badge pages found.  Gathering additional data")
        currentpage = 2
        while currentpage <= badgePages:
            r = requests.get(myProfileURL+"/badges/?p=" +
                             str(currentpage), cookies=cookies)
            badgePageData = bs4.BeautifulSoup(r.text)
            badgeSet = badgeSet + \
                badgePageData.find_all("div", {"class": "badge_title_stats"})
            currentpage = currentpage + 1
except:
    logging.warning("Reading badge page, please wait")

userinfo = badgePageData.find("a", {"class": "user_avatar"})
if not userinfo:
    logging.warning(
        Fore.RED + "Invalid cookie data, cannot log in to Steam" + Fore.RESET)
    raw_input("Press Enter to continue...")
    sys.exit()

if authData["sort"] == "mostvalue" or authData["sort"] == "leastvalue":
    logging.warning("Getting card values, please wait...")

for badge in badgeSet:
    try:
        badge_text = badge.get_text()
        dropCount = badge.find_all("span", {"class": "progress_info_bold"})[
            0].contents[0]
        has_playtime = re.search("[0-9\.] hrs on record", badge_text) != None

        if "No card drops" in dropCount or (has_playtime == False and authData["hasPlayTime"].lower() == "true"):
            continue
        else:
            # Remaining drops
            dropCountInt, junk = dropCount.split(" ", 1)
            dropCountInt = int(dropCountInt)
            linkGuess = badge.find_parent().find_parent().find_parent().find_all("a")[0]["href"]
            junk, badgeId = linkGuess.split("/gamecards/", 1)
            badgeId = int(badgeId.replace("/", ""))

            if authData["sort"] == "mostvalue" or authData["sort"] == "leastvalue":
                gameValue = requests.get(
                    "http://api.enhancedsteam.com/market_data/average_card_price/?appid=" + str(badgeId) + "&cur=usd")
                push = [badgeId, dropCountInt, float(str(gameValue.text))]
                badgesLeft.append(push)
            else:
                push = [badgeId, dropCountInt, 0]
                badgesLeft.append(push)
    except:
        continue

logging.warning("Idle Master needs to idle " + Fore.GREEN +
                str(len(badgesLeft)) + Fore.RESET + " games")


def getKey(item):
    if authData["sort"].endswith('cards'):
        return item[1]
    elif authData["sort"].endswith('value'):
        return item[2]
    else:
        return item[0]


sortValues = ["", "mostcards", "leastcards", "mostvalue", "leastvalue"]
if authData["sort"] in sortValues:
    if authData["sort"] == "":
        games = badgesLeft
    if authData["sort"].startswith('most'):
        games = sorted(badgesLeft, key=getKey, reverse=True)
    if authData["sort"].startswith('least'):
        games = sorted(badgesLeft, key=getKey, reverse=False)
else:
    logging.warning(Fore.RED + "Invalid sort value" + Fore.RESET)
    raw_input("Press Enter to continue...")
    sys.exit()

for appID, drops, value in games:
    delay = DROP_DELAY
    stillHaveDrops = 1
    numCycles = 50
    maxFail = 2

    idleOpen(appID)

    logging.warning(getAppName(appID) + " has " +
                    str(drops) + " card drops remaining")

    while stillHaveDrops == 1:
        try:
            logging.warning("Sleeping for " + str(delay / 60) + " minutes")
            time.sleep(delay)
            numCycles -= 1
            if numCycles < 1:  # Sanity check against infinite loop
                stillHaveDrops = 0

            logging.warning("Checking to see if " +
                            getAppName(appID) + " has remaining card drops")
            rBadge = requests.get(
                myProfileURL + "/gamecards/%s/" % str(appID), cookies=cookies)
            indBadgeData = bs4.BeautifulSoup(rBadge.text, 'html.parser')
            badgeLeftString = indBadgeData.find_all(
                "span", {"class": "progress_info_bold"})[0].contents[0]
            if "No card drops" in badgeLeftString:
                logging.warning("No card drops remaining")
                stillHaveDrops = 0
            else:
                dropCount, junk = badgeLeftString.split(" ", 1)
                logging.warning(getAppName(appID) + " has " +
                                dropCount + " card drops remaining")

        except:
            if maxFail > 0:
                logging.warning(
                    "Error checking if drops are done, number of tries remaining: " + str(maxFail))
                maxFail -= 1
            else:
                # Suspend operations until Steam can be reached.
                chillOut(appID)
                maxFail += 1
                break

    idleClose(appID)
    logging.warning(Fore.GREEN + "Successfully completed idling cards for " +
                    getAppName(appID) + Fore.RESET)

logging.warning(
    Fore.GREEN + "Successfully completed idling process" + Fore.RESET)
raw_input("Press Enter to continue...")
