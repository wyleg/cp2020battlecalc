#!/usr/bin/python3

import random, json, os, re, sys
from shutil import copyfile

global charlist

def getCurrentRound():
    rounds = os.listdir("rounds")
    rounds.sort()

    cur_round = int(rounds[-1])
    return cur_round

def loadRoundData(c_round):
    global charlist
    character_files = os.listdir("rounds/{}".format(c_round))
    for filename in character_files:
        if not ".log" in filename:
            with open("rounds/{}/{}".format(c_round, filename), "r") as char_file:
                char_json = json.loads(char_file.read())
                char_name = char_json["name"]
                charlist.update( { char_name: Character(**char_json) } )

def getRoundInfo():
    print("Round {}".format(cur_round))
    print(list(charlist))

def makeNextRound():
    next_round = cur_round + 1
    os.mkdir("rounds/"+str(next_round))
    prev_round_chars = os.listdir("rounds/"+str(cur_round))
    for char in prev_round_chars:
        with open("rounds/{}/{}".format(cur_round, char), "r") as charsheet_file:
            charsheet = json.loads(charsheet_file.read())
            if charsheet["state"] != "dead":
                copyfile("rounds/{}/{}".format(cur_round, char),"rounds/{}/{}".format(next_round, char))
    print("Started new round {}".format(next_round))

def shootParseArgs(arg_list):
    cover=""
    if arg_list[0] in list(charlist):
        character = charlist[arg_list[0]]
    else:
        print("No such character in this round")
        return
    if arg_list[0] in list(charlist):
        target = charlist[arg_list[1]]
    else:
        print("No such target in this round")
        return
    distance = int(arg_list[2])
    preroll = 0
    nosaveroll = False
    firemode = "s"
    bodypart = "random"
    burst_size = 0
    cm = 0
    for arg in arg_list:
        if re.match("^pr=.*", arg):
            preroll = int(re.sub("pr=","",arg))
        elif re.match("^cm=.*", arg):
            cm = int(re.sub("cm=","",arg))
        elif arg == "ns":
            nosaveroll = True
        elif re.match("^f=.*", arg):
            firemode = "f"
            burst_size = int(re.sub("f=","",arg))
        elif arg == "b":
            firemode = "b"
        elif re.match("^bp=.*", arg):
            bodypart = re.sub("bp=","",arg)
        elif re.match("^cvr=.*", arg):
            cover = re.sub("cvr=","",arg)
    print(character.Shoot(target, distance, firemode, cover, burst_size, preroll, bodypart, cm, nosaveroll))
    save_results = input("Write results? y/n: ")

    if save_results == "y":
        writeData()

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

def writeData():
    for char in list(charlist):
        char_dict = writeCharDataToDict(char)
        with open("rounds/{}/{}".format(cur_round, char), "w") as char_file:
            char_file.write(json.dumps(char_dict, indent=3))

def writeCharDataToDict(char_name):
    character = charlist[char_name]
    char_dict = {}
    char_dict.update( { "name": character.name,
        "role": character.role,
        "state": character.state,
        "wounded": character.wounded,
        "notes": character.notes,
        "hp": character.hp,
        "blunt_dmg": character.blunt_dmg,
        "EV": character.EV,
        "initiative": character.initiative,
        "current_weapon": character.current_weapon,
        "armor": character.armor,
        "stats": character.stats,
        "skills": character.skills,
        "weapons": character.weapons,
        "ammo": character.ammo
        } )
    return char_dict

def calculateInitiative(overwrite=False):
    global charlist
    for char_name in list(charlist):
        char = charlist[char_name]
        if ( char.initiative == 0 or overwrite ) and char.state != "dead":
            char.RollInitiative()
    writeData()

def getRoundOrder():
    init_dict = {}
    for char_name in charlist:
        char = charlist[char_name]
        init_dict.update( { char_name: char.initiative } )
    
    for i in sorted(init_dict, key=init_dict.get, reverse=True):
        print(i, init_dict[i], charlist[i].state)

class Character:

    def __init__(self, name, role, armor, stats, skills, weapons, ammo, current_weapon="", state="active", wounded="no", hp=40, blunt_dmg=0, EV=0, notes="", initiative=0):
        self.name = name
        self.role = role
        self.state = state
        self.wounded = wounded
        self.hp = hp
        self.blunt_dmg = blunt_dmg
        self.EV = EV
        self.armor = armor
        self.stats = stats
        self.skills = skills
        self.weapons = weapons
        self.ammo = ammo
        self.notes = notes
        self.initiative = initiative

        if current_weapon == "":
            self.current_weapon = list(weapons)[0]
        else:
            self.current_weapon = current_weapon

    def RollInitiative(self):
        mod = 0
        if "Combat Sense" in self.skills:
            mod += self.skills["Combat Sense"]
        mod += self.GetStatValue("REF")

        initiative = dice(10, True) + mod
        self.initiative = initiative

    def GetBTM(self):
        bt = self.stats["BT"]
        if bt <= 2:
            btm = 0
        elif bt == 3 or bt == 4:
            btm = 1
        elif bt >= 5 and bt <= 7:
            btm = 2
        elif bt == 8 or bt == 9:
            btm = 3
        elif bt == 10:
            btm = 4

        return btm

    def UpdateWoundState(self):
        dmg = 40 - self.hp
        if dmg == 0:
            self.wounded = "no"
        elif dmg >= 1 and dmg <= 4:
            self.wounded = "light"
        elif dmg >= 5 and dmg <= 8:
            self.wounded = "serious"
        elif dmg >= 9 and dmg <= 12:
            self.wounded = "critical"
        elif dmg >= 13 and dmg <= 16:
            self.wounded = "mortal 0"
        elif dmg >= 17 and dmg <= 20:
            self.wounded = "mortal 1"
        elif dmg >= 21 and dmg <= 24:
            self.wounded = "mortal 2"
        elif dmg >= 25 and dmg <= 28:
            self.wounded = "mortal 3"
        elif dmg >= 29 and dmg <= 32:
            self.wounded = "mortal 4"
        elif dmg >= 33 and dmg <= 36:
            self.wounded = "mortal 5"
        elif dmg >= 37 and dmg <= 40:
            self.wounded = "mortal 6"

        if "severed" in self.notes and not "mortal" in self.wounded:
            self.wounded = "mortal 0"
        
        if dmg > 40:
            self.state = "dead"

    def SwitchWeapon(self, weapon):
        if weapon in self.weapons:
            self.current_weapon = weapon
        else:
            print("{} don't have that weapon in inventory".format(self.name))

    def GetInfo(self):
        message = "{} [{}], {}, HP {}, {} wounds {}".format(self.name, self.role, self.state, self.hp, self.wounded, self.notes)
        if self.blunt_dmg > 0:
            message += " {} blunt damage".format(self.blunt_dmg)
        message += re.sub("{|'|}", "", re.sub("},", "\n", "\nArmor:\n {}\n".format(self.armor)))
        message += "Equipped with {} [{}/{} rds]\n"\
            .format(self.current_weapon, self.weapons[self.current_weapon]["mag"], WEAPONS[self.current_weapon]["Shots"])

        return message

    def GetStatValue(self, stat):
        EV = 0
        def woundMod(stat):
            stat_mod = 0
            if stat == "CL" or stat == "REF" or stat == "MA" or stat == "INT":
                wound = self.wounded
                if wound == "serious" and stat == "REF":
                    stat_mod = 2
                elif wound == "critical":
                    stat_mod = int(self.stats["REF"]/2)
                elif "mortal" in wound:
                    stat_mod = int(2*self.stats["REF"]/3)
            return stat_mod

        if stat == "REF":
            EV = self.EV

        return self.stats[stat] - woundMod(stat) - EV

    def SkillStatValue(self, skill):
        result = 0
        skill = skillShortcut(skill)

        stat = getStatBySkill(skill)
        stat_value = self.GetStatValue(stat)
        skill_value = self.skills[skill]
        result = skill_value + stat_value

        return result, stat

    def SkillRoll(self, skill, cm=0):
        skill = skillShortcut(skill)
        value, stat = self.SkillStatValue(skill)
        diceroll = dice(10)

        result = value + diceroll + cm

        message = "{} rolls {} check: {} {} + skill {} + d10({}) + modifier {} = {}\n".\
            format(self.name, skill, stat, self.stats[stat], self.skills[skill], diceroll, cm, result)

        return result, message, diceroll

    def SkillCheck(self, skill, difficulty, cm=0):
        skill = skillShortcut(skill)
        success = False
        outcome = "failed"
        message = ""

        roll, message, diceroll = self.SkillRoll(skill, cm)
        message = message.rstrip("\n")

        if diceroll == 1:
            message = "CRIT FAIL\n"
        else:
            if roll >= difficulty:
                success = True
                outcome = "success"
            
            message += " vs {} difficulty  - {}\n".\
                format(difficulty, outcome)
        
        return success, message
            
    def StunSave(self):
        success = False
        outcome = ""
        stun_mod = { "no": 0,
                "light": 0,
                "serious": 1,
                "critical": 2,
                "mortal 0": 3,
                "mortal 1": 4,
                "mortal 2": 5,
                "mortal 3": 6,
                "mortal 4": 7,
                "mortal 5": 8,
                "mortal 6": 9 }

        treshhold = self.GetStatValue("BT") - stun_mod[self.wounded]
        diceroll = dice(10, True)

        if diceroll <= treshhold:
            success = True
            outcome = "success"
        else:
            success = False
            outcome = "failed"

        message = "{} rolls stun save: {} vs d10({}) (BT {}, stun_mod {}) - {}\n"\
            .format(self.name, treshhold, diceroll, self.GetStatValue("BT"), stun_mod[self.wounded], outcome)

        return success, message

    def DeathSave(self):
        if "mortal" in self.wounded:
            mortal_mod = int(re.split(" ", self.wounded)[1])
        else:
            mortal_mod = 0

        treshhold = self.GetStatValue("BT") - mortal_mod
        diceroll = dice(10, True)

        if diceroll <= treshhold:
            success = True
            outcome = "success"
        else:
            success = False
            outcome = "failed"

        message = "{} rolls death save: {} vs d10({}) (BT {}, mortal_mod {}) - {}\n"\
            .format(self.name, treshhold, diceroll, self.GetStatValue("BT"), mortal_mod, outcome)

        return success, message

    def Damage(self, bodypart, damage_stat, ammo_type, cover="", nosaveroll=False):
        message = ""
        cover_sp = 0
        effective_cover_sp = 0
        severed = False
        armor_zone = bodypart
        armor_type = self.armor[armor_zone]["type"]

        btm = self.GetBTM()

        dmg_parts = re.split("D", damage_stat)
        try:
            dmg_dice = int(re.split(r"\+", dmg_parts[1])[0])
            dmg_add = int(re.split(r"\+", dmg_parts[1])[1])
        except:
            dmg_dice = int(dmg_parts[1])
            dmg_add = 0
 
        dmg_num = int(dmg_parts[0])

        damage_output = damage_stat+": "
        damage_raw = 0
        for _ in range(0, dmg_num):
            dmg_inc = dice(dmg_dice)
            damage_raw += dmg_inc
            damage_output += str(dmg_inc)+" + "

        damage_raw += dmg_add
        damage_output += str(dmg_add)

        if cover != "":
            cover_sp = COVERS[cover]
            if ammo_type == "ap" or ammo_type == "slug":
                effective_cover_sp = cover_sp - int(cover_sp/2)
            else:
                effective_cover_sp = cover_sp
            damage_raw -= effective_cover_sp
            if ammo_type == "ap":
                damage_raw = damage_raw - int(damage_raw/2)
            #message += "Damage reduced to {} by {} with SP {}\n".format(damage_raw, cover, cover_sp)
            damage_output += " (hard cover {} SP)".format(cover_sp)

        sp = self.armor[armor_zone]["SP"]
        effective_sp = sp

        if ammo_type == "ap" or ammo_type == "slug":
            effective_sp -= int(sp/2)

        damage_output += " = "+str(damage_raw)+" | "+str(sp)+" SP | "+str(btm)+" BTM"

        if damage_raw > effective_sp:

            damage = damage_raw - effective_sp

            if bodypart == "head":
                damage *= 2

            if ammo_type == "ap" or ( ammo_type == "slug" and ( armor_type == "soft" or armor_type == "no" ) ):
                damage -= int(damage/2)

            damage -= btm

            if damage < 1:
                damage = 1
                self.blunt_dmg += 1
            if armor_type != "no" or self.armor[armor_zone]["SP"] > 0:
                self.armor[armor_zone]["SP"] -= 1
            self.hp -= damage

            self.UpdateWoundState()

            if damage > 8 and bodypart != "torso":
                message += "More than 8 damage to limb!"
                severed = True

            if nosaveroll or self.state == "dead":
                return damage, damage_output, message+"\n"

            if severed:
                stun_roll_success, stun_roll_msg = self.StunSave()
                message += " "+stun_roll_msg
                if stun_roll_success == False:
                    message += "Stun roll failed, {} is severed. ".format(bodypart)
                    self.notes += "{} severed;".format(bodypart)
                    if bodypart == "head":
                        self.state = "dead"
                        return damage, damage_output, message+"\n"
                    else:
                        death_save_success, death_save_msg = self.DeathSave()
                        if not death_save_success:
                            self.state = "dead"
                            message += death_save_msg

                            return damage, damage_output, message

                        message += death_save_msg

            if "mortal" in self.wounded:
                death_save_success, death_save_msg = self.DeathSave()
                if not death_save_success:
                    self.state = "dead"
                    message += death_save_msg
                    return damage, damage_output, message

                message += death_save_msg

            self.UpdateWoundState()

            if self.state == "active":
                stun_roll_success, stun_roll_msg = self.StunSave()
                message += stun_roll_msg
                if stun_roll_success == True:
                    self.state = "active"
                else:
                    self.state = "stunned"
                
        else:
            damage = 0

        return damage, damage_output, message

    def Shoot(self, target_name, distance, firemode="s", cover="", burst_size=0, preroll=0, bodypart="random", cm=0, nosaveroll=False):
        # s - single fire
        # b - burst fire
        # f - full auto

        def calculateShotDamage(target, cover, bodypart, ammo_type):
            message = ""
            if bodypart == "random":
                bodypart = rollBodypart()
                while "{} severed".format(bodypart) in target.notes:
                    message += "{}'s {} is severed, rerolling bodypart\n".format(target.name, bodypart)
                    bodypart = rollBodypart()
            damage, damage_output, damage_report = target.Damage(bodypart, WEAPONS[self.current_weapon]["Damage"], ammo_type, cover, nosaveroll)
            message += "Dealt {} damage to the {} [{}], target HP is {} ({}; {})\n".format(damage, bodypart, damage_output, target.hp, target.state, target.wounded)
            message += damage_report

            return message

        if type(target_name) == str:
            target = charlist[target_name]
        elif type(target_name) == Character:
            target = target_name
        firemode_mod = 0
        firemode_msg = ""
        effective_cover = ""

        if bodypart != "random":
            if "{} severed".format(bodypart) in target.notes:
                message = "{}'s {} is already severed, choose another bodypart\n".format(target.name, bodypart)
                return message

        if self.state != "active":
            return "{} is {} and can't shoot\n".format(self.name, self.state)

        if self.weapons[self.current_weapon]["mag"] < 3 and firemode == "b":
            return "Not enough ammo for 3 round burst\n"

        if self.weapons[self.current_weapon]["mag"] == 0:
            return "No ammo\n"
        else:
            ammo_type = self.weapons[self.current_weapon]["ammotype"]

            if bodypart != "random":
                bodypart_message = "'s {}".format(bodypart)
            else:
                bodypart_message = ""

            message = "{} firing at {}{} with {} ({}, {}) [{}/{} rds]"\
                .format(self.name, target.name, bodypart_message, self.current_weapon, firemode, \
                    ammo_type, self.weapons[self.current_weapon]["mag"], WEAPONS[self.current_weapon]["Shots"])

            if preroll == 0:
                diceroll = dice(10)
                message += "\n"
            else:
                diceroll = preroll
                message += " (prerolled dice {})\n".format(diceroll)

            if diceroll == 1:
                message += "CRIT FAIL\n"
            else:
                difficulty = getDifficultyByRange(self.current_weapon, distance)

                # ЕСЛИ НЕТ СКИЛЛА НА СТРЕЛЬБУ ИЗ НУЖНОЙ ПУШКИ

                if firemode == "b" and difficulty <= 20:
                    firemode_mod = 3
                    firemode_msg = " + 3 (burst fire)"
                elif firemode == "f":
                    if burst_size > self.weapons[self.current_weapon]["mag"]:
                        message += "Not enough ammo in magazine\n"
                        return message
                    if difficulty <= 15: # only at close range
                        firemode_mod = int(burst_size / 10)
                    else:
                        firemode_mod = -int(burst_size / 10)
                    firemode_msg = " + fullauto({})".format(firemode_mod)

                weapontype = WEAPONS[self.current_weapon]["Type"]
                message += "Gun range: {}, distance to target: {}, difficulty: {}\n"\
                    .format(WEAPONS[self.current_weapon]["Range"], distance, difficulty)

                message += "REF({}) + {}({}) + WA({}) + d10({}){}"\
                    .format(self.GetStatValue("REF"), weapontype, self.skills[weapontype], WEAPONS[self.current_weapon]["WA"], diceroll, firemode_msg)

                if cm != 0:
                    message += " + custom_mod({})".format(cm)

                if bodypart != "random":
                    bodypart_mod = -4
                    message += " - bodypart(4)"
                else:
                    bodypart_mod = 0
                    bodypart = rollBodypart()
                    while "{} severed".format(bodypart) in target.notes:
                        message += "{}'s {} is severed, rerolling bodypart\n".format(target.name, bodypart)
                        bodypart = rollBodypart()

                result = self.GetStatValue("REF") + self.skills[weapontype] + diceroll + WEAPONS[self.current_weapon]["WA"] + bodypart_mod + firemode_mod + cm
                message += " = {}\n".format(result)

                if result >= difficulty:
                    if cover != '':
                        add_cover = input("Hit {} in the {}, apply cover? (y/n) ".format(target.name, bodypart))
                        if add_cover == "y":
                            effective_cover = cover
                        else:
                            effective_cover = ""

                    if firemode == "s":
                        message += calculateShotDamage(target, effective_cover, bodypart, ammo_type)
                        self.weapons[self.current_weapon]["mag"] -= 1

                    elif firemode == "b":
                        hit_count = dice(3)
                        message += calculateShotDamage(target, effective_cover, bodypart, ammo_type)
                        hit_count -= 1
                        message += "{} more hits in burst\n".format(hit_count)
                        for _ in range(0, hit_count):
                            bodypart = rollBodypart()
                            while "{} severed".format(bodypart) in target.notes:
                                message += "{}'s {} is severed, rerolling bodypart\n".format(target.name, bodypart)
                                bodypart = rollBodypart()
                            if cover != '':
                                add_cover = input("Hit {} in the {}, apply cover? (y/n) ".format(target.name, bodypart))
                                if add_cover == "y":
                                    effective_cover = cover
                                else:
                                    effective_cover = ""
                            message += calculateShotDamage(target, effective_cover, bodypart, ammo_type)
                        self.weapons[self.current_weapon]["mag"] -= 3

                    elif firemode == "f":
                        print("Result: {}".format(result))
                        print("Difficulty: {}".format(difficulty))
                        hit_count = result - difficulty + 1
                        if hit_count > burst_size:
                            hit_count = burst_size
                        message += "{} hits in full auto burst\n".format(hit_count)
                        for _ in range(0, hit_count):
                            bodypart = rollBodypart()
                            while "{} severed".format(bodypart) in target.notes:
                                message += "{}'s {} is severed, rerolling bodypart\n".format(target.name, bodypart)
                                bodypart = rollBodypart()
                            if cover != '':
                                add_cover = input("Hit {} in the {}, apply cover? (y/n) ".format(target.name, bodypart))
                                if add_cover == "y":
                                    effective_cover = cover
                                else:
                                    effective_cover = ""
                            message += calculateShotDamage(target, effective_cover, bodypart, ammo_type)
                        self.weapons[self.current_weapon]["mag"] -= burst_size


                else:
                    message += "Missed\n"
                    self.weapons[self.current_weapon]["mag"] -= 1

                message += "Rounds left in mag: {}\n".format(self.weapons[self.current_weapon]["mag"])
            return message

    # end of Character class


with open("weapons.json", "r") as weapons_file:
    WEAPONS = json.loads(weapons_file.read())

with open("skills.json", "r") as skills_file:
    SKILLS = json.loads(skills_file.read())

with open("covers.json", "r") as covers_file:
    COVERS = json.loads(covers_file.read())

charlist = {}

cur_round = getCurrentRound()
loadRoundData(cur_round)


def executeCommand(args):
    print(args)
    cmd = args[0]
    args_list = args
    args_list.pop(0)
    if cmd == "exit":
        sys.exit(0)
    if cmd == "help":
        print("Commands:\n\
    getroundinfo\n\
    getcharinfo <character>\n\
    nextround\n\
    shoot <character> <target> <distance> [preroll=<number>] [ns] [cm=<modifier>] [f=<fullauto_burst_size>|b|s] [bp=<bodypart>]\n")
    elif cmd == "getroundinfo":
        getRoundInfo()
    elif "shoot" in cmd:
        shootParseArgs(args_list)
    elif cmd == "nextround":
        makeNextRound()
    elif cmd == "getcharinfo":
        print(charlist[args_list[0]].GetInfo())
    elif cmd == "calcinit":
        overwrite = False
        if "ow" in args_list:
            overwrite = True
        calculateInitiative(overwrite)
    elif cmd == "getroundorder":
        getRoundOrder()

if len(sys.argv) > 1:
    args_list = list(sys.argv)
    args_list.pop(0)
    executeCommand(args_list)
else:
    while True:
        cmd = input("> ")
        arg_list = re.split(" ",cmd)
        executeCommand(arg_list)