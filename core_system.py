#!/usr/bin/python3

import random, json

def dice(num, not_explode=False):
    result = random.randint(1,num)
    if num == 10:
        if result == 10 and not_explode == False:
            result += dice(num)
    return result

def rollBodypart():
    bodypart_roll = dice(10, True)
    if bodypart_roll == 1:
        bodypart = "head"
    elif bodypart_roll >= 2 and bodypart_roll <= 4:
        bodypart = "torso"
    elif bodypart_roll == 5:
        bodypart = "r_arm"
    elif bodypart_roll == 6:
        bodypart = "l_arm"
    elif bodypart_roll >= 7 and bodypart_roll <= 8:
        bodypart = "r_leg"
    elif bodypart_roll >= 9 and bodypart_roll <= 10:
        bodypart = "l_leg"

    return bodypart

def skillShortcut(skill):
    if skill == "awrn":
        skill = "Awareness/Notice"
    return skill

def getStatBySkill(skill):
    skill = skillShortcut(skill)
    resp_stat = ""
    for stat in list(SKILLS):
        if skill in SKILLS[stat]:
            resp_stat = stat
    return resp_stat

def getDifficultyByRange(gun_name, distance):
    if distance <= 1:
        difficulty = 10
    else:
        gun_range = WEAPONS[gun_name]["Range"]
        rd_ratio = distance / gun_range
        if rd_ratio > 2:
            difficulty = 100
        elif rd_ratio > 1:
            difficulty = 30
        elif rd_ratio > 0.5:
            difficulty = 25
        elif rd_ratio > 0.25:
            difficulty = 20
        else:
            difficulty = 15
    return difficulty

with open("weapons.json", "r") as weapons_file:
    WEAPONS = json.loads(weapons_file.read())

with open("skills.json", "r") as skills_file:
    SKILLS = json.loads(skills_file.read())