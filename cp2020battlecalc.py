#!/usr/bin/python3

import random, json

def dice(num):
    return random.randint(1,num)

class Character:

    class weapon:
        model = ""
        ammo_mag = 0

    def __init__(self, name, role, stats_dict, skills_dict, weapon):
        self.name = name
        self.role = role
        self.hp = 40
        
        self.stats = stats_dict
        self.skills = skills_dict

        self.weapon.model = weapon
        self.weapon.ammo_mag = WEAPONS[weapon]["Shots"]


    def shoot(self):

        diceroll = dice(10)
        weapontype = WEAPONS[self.weapon.model]["Type"]
        result = self.stats["REF"] + self.skills["REF"]["Rifle"] + diceroll
        message = "Firing with {}\nREF {} + {} {} + d10 {} = {}".format(self.weapon.model, self.stats["REF"], weapontype, self.skills["REF"][weapontype], diceroll, result)

        return message


with open("weapons.json", "r") as weapons_file:
    WEAPONS = json.loads(weapons_file.read())




samplestats = {
    "INT": 0,
    "REF": 9,
    "CL": 0,
    "TECH": 0,
    "LK": 0,
    "ATT": 0,
    "MA": 0,
    "EMP": 0,
    "BT": 0
        }

sampleskills = {
        "Career": {
            "Combat Sense": 6
            },
        "REF": {
            "Rifle": 6
            },
        "INT": {
            "Awareness/Notice": 6
            }
        }

Bob = Character("Bob", "Solo", samplestats, sampleskills, "FN-RAL")


print(Bob.shoot())

#print(d10())



