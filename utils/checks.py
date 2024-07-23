import json
from discord.ext import commands
import time
import asyncio

STAFF = [
  980721105629220874
]
def getConfig(userID):
    with open("utils/data.json", "r") as config:
        data = json.load(config)
    if str(userID) not in data["guilds"]:
        defaultConfig = {
            "private": "None",
            "addy": "None",
            "id": "None",
            "owner": 0,
            "reciev": 1,
            "amount": 0,
            "conf1": 0,
            "conf2": 0
        }
        updateConfig(userID, defaultConfig)
        return defaultConfig
    return data["guilds"][str(userID)]


def updateConfig(userID, data):
    with open("utils/data.json", "r") as config:
        config = json.load(config)
    config["guilds"][str(userID)] = data
    newdata = json.dumps(config, indent=4, ensure_ascii=False)
    with open("utils/data.json", "w") as config:
        config.write(newdata)

def getpro(userID):
  with open("utils/pro.json", "r") as config:
    data = json.load(config)
  if str(userID) not in data["guilds"]:
    defaultConfig = {
        "badges": [],
        "deals": 0,
        "amount": 0
    }
    updatepro(userID, defaultConfig)
    return defaultConfig
  return data["guilds"][str(userID)]


def updatepro(userID, data):
  with open("utils/pro.json", "r") as config:
      config = json.load(config)
  config["guilds"][str(userID)] = data
  newdata = json.dumps(config, indent=4, ensure_ascii=False)
  with open("utils/pro.json", "w") as config:
      config.write(newdata)

def staff_only():
    async def predicate(ctx):
      return ctx.author.id in STAFF
    return commands.check(predicate)