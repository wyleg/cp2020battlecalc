#!/usr/bin/python3

import random, json, os, re

def dice(num, not_explode=False):
    result = random.randint(1,num)
    if num == 10:
        if result == 10 and not_explode == False:
            result += dice(num)
    return result

class Character:

    def __init__(self, name, role, hp, EV, armor, stats, skills, weapons, ammo):
        self.name = name
        self.role = role
        self.hp = hp
        self.EV = EV
        self.armor = armor
        self.stats = stats
        self.skills = skills
        self.weapons = weapons
        self.ammo = ammo

        self.current_weapon = list(weapons)[0]

    def SwitchWeapon(self, weapon):
        if weapon in self.weapons:
            self.current_weapon = weapon
        else:
            print("{} don't have that weapon in inventory".format(self.name))


    def GetInfo(self):
        message = "{} [{}] HP {}\n".format(self.name, self.role, self.hp)
        message += re.sub("{|'|}", "", re.sub("},", "\n", "Armor:\n {}\n".format(self.armor)))
        message += "Equipped with {} [{}/{} rds]\n"\
            .format(self.current_weapon, self.weapons[self.current_weapon]["mag"], WEAPONS[self.current_weapon]["Shots"])

        return message

    def Damage(self, bodypart, damage_stat):
        armor_zone = bodypart

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
        for i in range(0, dmg_num):
            dmg_inc = dice(dmg_dice)
            damage_raw += dmg_inc
            damage_output += str(dmg_inc)+" + "

        damage_raw += dmg_add
        damage_output += str(dmg_add)

        sp = self.armor[armor_zone]["SP"]

        damage_output += " = "+str(damage_raw)+" | "+str(sp)+" SP | "+str(btm)+" BTM"

        if damage_raw > sp:
            

            damage = damage_raw - sp - btm
            
            if damage < 1:
                damage = 1
            self.armor[armor_zone]["SP"] -= 1
            self.hp -= damage
        else:
            damage = 0

            # ОТРЫВ КОНЕЧНОСТЕЙ

            # СПАСБРОСКИ

        return damage, damage_output, self.hp


    def Shoot(self, target_name, distance, firemode="s", burst_size=0, preroll=0, bodypart="random", cm=0):
        # s - single fire
        # b - burst fire
        # f - full auto

        target = charlist[target_name]

        if self.weapons[self.current_weapon]["mag"] > 0:

            if bodypart != "random":
                bodypart_message = "'s {}".format(bodypart)
            else:
                bodypart_message = ""

            message = "{} firing at {}{} with {} ({}) [{}/{} rds]"\
                .format(self.name, target_name, bodypart_message, self.current_weapon, firemode, self.weapons[self.current_weapon]["mag"], WEAPONS[self.current_weapon]["Shots"])

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
                    .format(self.stats["REF"], weapontype, self.skills["REF"][weapontype], self.EV, WEAPONS[self.current_weapon]["WA"], diceroll)

                if bodypart != "random":
                    bodypart_mod = -4
                    message += " - bodypart(4)"
                else:
                    bodypart_mod = 0

                result = self.stats["REF"] + self.skills["REF"][weapontype] + diceroll + WEAPONS[self.current_weapon]["WA"] - self.EV + bodypart_mod

                self.weapons[self.current_weapon]["mag"] -= 1

                message += " = {}\n".format(result)
              
                if result > difficulty:
                    if bodypart == "random":
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
                    
                    damage, damage_output, target_health = target.Damage(bodypart, WEAPONS[self.current_weapon]["Damage"])
                    message += "Dealt {} damage to the {} [{}], target HP is {}\n".format(damage, bodypart, damage_output, target_health)
                else:
                    message += "Missed\n"

                message += "Rounds left in mag: {}\n".format(self.weapons[self.current_weapon]["mag"])
            return message


with open("weapons.json", "r") as weapons_file:
    WEAPONS = json.loads(weapons_file.read())

character_files = os.listdir("characters")

charlist = {}

for char in character_files:
    with open("characters/" + char, "r") as char_file:
        charlist.update( { char: Character(**json.loads(char_file.read())) } )

Bob = charlist["Bob"]
Alice = charlist["Alice"]

print(Bob.GetInfo())

Bob.SwitchWeapon("X-9mm")

print(Bob.Shoot("Alice", 1, bodypart="r_leg"))
print(Bob.Shoot("Alice", 1, bodypart="r_leg"))
print(Bob.Shoot("Alice", 1, bodypart="r_leg"))
print(Bob.Shoot("Alice", 1, bodypart="r_leg"))
print(Bob.Shoot("Alice", 5, preroll=9))
print(Bob.Shoot("Alice", 15))

print(Alice.GetInfo())

Bob.SwitchWeapon("FN-RAL")






#print(d10())



