#!/usr/bin/python3

import random, json, os, re, sys

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


class Character:

    def __init__(self, name, role, armor, stats, skills, weapons, ammo, state="active", wounded="no", hp=40, blunt_dmg=0, EV=0, notes=""):
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

        self.current_weapon = list(weapons)[0]

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

        return self.stats[stat] - woundMod(stat)

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


    def Damage(self, bodypart, damage_stat, ammo_type, nosaveroll=False):
        message = ""
        severed = False
        armor_zone = bodypart

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

        sp = self.armor[armor_zone]["SP"]
        effective_sp = sp

        if ammo_type == "ap":
            effective_sp -= int(sp/2)

        damage_output += " = "+str(damage_raw)+" | "+str(sp)+" SP | "+str(btm)+" BTM"

        if damage_raw > effective_sp:

            damage = damage_raw - effective_sp

            if bodypart == "head":
                damage *= 2

            if ammo_type == "ap":
                damage -= int(damage/2)

            damage -= btm

            if damage < 1:
                damage = 1
                self.blunt_dmg += 1
            self.armor[armor_zone]["SP"] -= 1
            self.hp -= damage

            self.UpdateWoundState()

            if damage > 8 and bodypart != "torso":
                message += "More than 8 damage to limb!\n"
                severed = True

            if nosaveroll:
                return damage, damage_output, message

            if severed:
                stun_roll_success, stun_roll_msg = self.StunSave()
                message += " "+stun_roll_msg
                if stun_roll_success == False:
                    message += "Stun roll failed, {} is severed. ".format(bodypart)
                    self.notes += "{} severed;".format(bodypart)
                    if bodypart == "head":
                        self.state = "dead"
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


    def Shoot(self, target_name, distance, firemode="s", burst_size=0, preroll=0, bodypart="random", cm=0, nosaveroll=False):
        # s - single fire
        # b - burst fire
        # f - full auto

        target = charlist[target_name]

        if self.state != "active":
            return "{} is {} and can't shoot\n".format(self.name, self.state)

        if self.weapons[self.current_weapon]["mag"] > 0:

            ammo_type = self.weapons[self.current_weapon]["ammotype"]

            if bodypart != "random":
                bodypart_message = "'s {}".format(bodypart)
            else:
                bodypart_message = ""

            message = "{} firing at {}{} with {} ({}, {}) [{}/{} rds]"\
                .format(self.name, target_name, bodypart_message, self.current_weapon, firemode, \
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
                # calculating difficulty by range
                if distance <= 1:
                    difficulty = 10
                else:
                    gun_range = WEAPONS[self.current_weapon]["Range"]
                    rd_ratio = distance / gun_range
                    if rd_ratio > 2:
                        message += "Too far!\n"
                        difficulty = 100
                    elif rd_ratio > 1:
                        difficulty = 30
                    elif rd_ratio > 0.5:
                        difficulty = 25
                    elif rd_ratio > 0.25:
                        difficulty = 20
                    else:
                        difficulty = 15

                # ЕСЛИ НЕТ СКИЛЛА НА СТРЕЛЬБУ ИЗ НУЖНОЙ ПУШКИ

                weapontype = WEAPONS[self.current_weapon]["Type"]
                message += "Gun range: {}, distance to target: {}, difficulty: {}\n"\
                    .format(WEAPONS[self.current_weapon]["Range"], distance, difficulty)

                message += "REF({}) + {}({}) - EV({}) + WA({}) + d10({})"\
                    .format(self.GetStatValue("REF"), weapontype, self.skills[weapontype], self.EV, WEAPONS[self.current_weapon]["WA"], diceroll)

                if bodypart != "random":
                    if "{} severed".format(bodypart) in target.notes:
                        message = "{}'s {} is already severed, choose another bodypart\n".format(target.name, bodypart)
                        return message

                    bodypart_mod = -4
                    message += " - bodypart(4)"
                else:
                    bodypart_mod = 0

                result = self.GetStatValue("REF") + self.skills[weapontype] + diceroll + WEAPONS[self.current_weapon]["WA"] - self.EV + bodypart_mod

                self.weapons[self.current_weapon]["mag"] -= 1

                message += " = {}\n".format(result)
              
                if result > difficulty:
                    if bodypart == "random":
                        bodypart = rollBodypart()
                        while "{} severed".format(bodypart) in target.notes:
                            message += "{}'s {} is severed, rerolling bodypart\n".format(target.name, bodypart)
                            bodypart = rollBodypart()

                    damage, damage_output, damage_report = target.Damage(bodypart, WEAPONS[self.current_weapon]["Damage"], ammo_type, nosaveroll)
                    message += "Dealt {} damage to the {} [{}], target HP is {} ({}; {})\n".format(damage, bodypart, damage_output, target.hp, target.state, target.wounded)
                    message += damage_report
                else:
                    message += "Missed\n"

                message += "Rounds left in mag: {}\n".format(self.weapons[self.current_weapon]["mag"])
            return message


with open("weapons.json", "r") as weapons_file:
    WEAPONS = json.loads(weapons_file.read())

with open("skills.json", "r") as skills_file:
    SKILLS = json.loads(skills_file.read())

character_files = os.listdir("characters")

charlist = {}

for char in character_files:
    with open("characters/" + char, "r") as char_file:
        charlist.update( { char: Character(**json.loads(char_file.read())) } )

Bob = charlist["Bob"]
Alice = charlist["Alice"]
print(Alice.GetInfo())

Bob.SwitchWeapon("H9")

print(Alice.SkillStatValue("awrn"))

print(Bob.Shoot("Alice", 1, nosaveroll=True))
print(Bob.Shoot("Alice", 1))
print(Bob.Shoot("Alice", 1))
print(Bob.Shoot("Alice", 1))
print(Bob.Shoot("Alice", 1))
print(Bob.Shoot("Alice", 1))
print(Bob.Shoot("Alice", 1))
#print(Bob.Shoot("Alice", 1))
#print(Bob.Shoot("Alice", 1))
##print(Bob.Shoot("Alice", 1, bodypart="r_leg"))
##print(Bob.Shoot("Alice", 1, bodypart="r_leg"))
#
#print(Alice.Shoot("Bob", 1))
#
##print(Bob.Shoot("Alice", 5, preroll=9))
##print(Bob.Shoot("Alice", 15))
#
print(Alice.GetInfo())
print(Bob.GetInfo())

print(Alice.SkillCheck("awrn", 15))

if len(sys.argv) > 1:
    if sys.argv[1] == "getinfo":
        character = charlist[sys.argv[2]]
        print(character.GetInfo())

    if sys.argv[1] == "shoot":
        character = charlist[sys.argv[2]]
        target = sys.argv[3]
        distance = int(sys.argv[4])
        preroll = 0
        nosaveroll = False
        firemode = "s"
        bodypart = "random"
        burst_size = 0
        cm = 0
        for arg in sys.argv:
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

        print(character.Shoot(target, distance, firemode, burst_size, preroll, bodypart, cm, nosaveroll))