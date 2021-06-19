import re

from core_system import dice, getDifficultyByRange, rollBodypart, skillShortcut, getStatBySkill, WEAPONS

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
        message = "{} [{}], {}, HP {}, BTM {}, {} wounds {}".format(self.name, self.role, self.state, self.hp, self.GetBTM(), self.wounded, self.notes)
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

    def GetSkillLevel(self, skill):
        if skill in list(self.skills):
            return self.skills[skill]
        else:
            return 0

    def SkillPlusStatValue(self, skill):
        result = 0
        skill = skillShortcut(skill)

        stat = getStatBySkill(skill)
        stat_value = self.GetStatValue(stat)
        if skill in list(self.skills):
            skill_value = self.skills[skill]
        else:
            skill_value = 0
        result = skill_value + stat_value

        return result, stat

    def SkillRoll(self, skill, cm=0):
        skill = skillShortcut(skill)
        value, stat = self.SkillPlusStatValue(skill)
        diceroll = dice(10)

        result = value + diceroll + cm

        message = "{} rolls {} check: {} {} + skill {} + d10({}) + modifier {} = {}\n".\
            format(self.name, skill, stat, self.stats[stat], self.GetSkillLevel(skill), diceroll, cm, result)

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

        treshold = self.GetStatValue("BT") - stun_mod[self.wounded]
        diceroll = dice(10, True)

        if diceroll <= treshold:
            success = True
            outcome = "success"
        else:
            success = False
            outcome = "failed"

        message = "{} rolls stun save: {} vs d10({}) (BT {}, stun_mod {}) - {}\n"\
            .format(self.name, treshold, diceroll, self.GetStatValue("BT"), stun_mod[self.wounded], outcome)

        return success, message

    def DeathSave(self):
        if "mortal" in self.wounded:
            mortal_mod = int(re.split(" ", self.wounded)[1])
        else:
            mortal_mod = 0

        treshold = self.GetStatValue("BT") - mortal_mod
        diceroll = dice(10, True)

        if diceroll <= treshold:
            success = True
            outcome = "success"
        else:
            success = False
            outcome = "failed"

        message = "{} rolls death save: {} vs d10({}) (BT {}, mortal_mod {}) - {}\n"\
            .format(self.name, treshold, diceroll, self.GetStatValue("BT"), mortal_mod, outcome)

        return success, message

    def Damage(self, bodypart, damage_stat, ammo_type, cover_sp, nosaveroll=False):
        message = ""
        effective_cover_sp = 0
        cover_penetrated = False
        severed_check = False
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

        if cover_sp != 0:
            if ammo_type == "ap" or ammo_type == "slug":
                effective_cover_sp = cover_sp - int(cover_sp/2)
            else:
                effective_cover_sp = cover_sp
            damage_raw -= effective_cover_sp
            if ammo_type == "ap":
                damage_raw = damage_raw - int(damage_raw/2)
            if damage_raw > 0:
                cover_penetrated = True
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
            if armor_type != "no" and self.armor[armor_zone]["SP"] > 0:
                self.armor[armor_zone]["SP"] -= 1
            self.hp -= damage

            self.UpdateWoundState()

            if damage > 8 and bodypart != "torso":
                message += "More than 8 damage to limb!"
                severed_check = True

            if nosaveroll or self.state == "dead":
                return damage, damage_output, message+"\n", cover_penetrated

            if severed_check:
                stun_roll_success, stun_roll_msg = self.StunSave()
                message += " "+stun_roll_msg
                if stun_roll_success == False:
                    message += "Stun roll failed, {} is severed. ".format(bodypart)
                    self.notes += "{} severed;".format(bodypart)
                    if bodypart == "head":
                        self.state = "dead"
                        return damage, damage_output, message+"\n", cover_penetrated
                    else:
                        death_save_success, death_save_msg = self.DeathSave()
                        if not death_save_success:
                            self.state = "dead"
                            message += death_save_msg

                            return damage, damage_output, message, cover_penetrated

                        message += death_save_msg

            if "mortal" in self.wounded:
                death_save_success, death_save_msg = self.DeathSave()
                if not death_save_success:
                    self.state = "dead"
                    message += death_save_msg
                    return damage, damage_output, message, cover_penetrated

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

        return damage, damage_output, message, cover_penetrated

    def Shoot(self, target: "Character", distance, burst_size, firemode="s", cover=0, preroll=0, bodypart="random", cm=0, nosaveroll=False):
        # s - single fire
        # b - burst fire
        # f - full auto

        def calculateShotDamage(target: "Character", cover, bodypart, ammo_type):
            message = ""
            if bodypart == "random":
                bodypart = rollBodypart()
                while "{} severed".format(bodypart) in target.notes:
                    bodypart = rollBodypart()
            damage, damage_output, damage_report, cover_penetrated = target.Damage(bodypart, WEAPONS[self.current_weapon]["Damage"], ammo_type, cover, nosaveroll)
            message += "= > Dealt {} damage to the {} [{}], target HP is {} ({}; {})\n".format(damage, bodypart, damage_output, target.hp, target.state, target.wounded)
            message += damage_report

            return message, cover_penetrated

        def MakeAShot(target, cover, bodypart, ammo_type):
            message = ""
            effective_cover = 0
            if bodypart == "random":
                bodypart = rollBodypart()
                while "{} severed".format(bodypart) in target.notes:
                    bodypart = rollBodypart()
            if cover != '':
                add_cover = input("Hit {} in the {}, apply cover? (y/n) ".format(target.name, bodypart))
                if add_cover == "y":
                    effective_cover = cover
            damage_report, cover_penetrated = calculateShotDamage(target, effective_cover, bodypart, ammo_type)
            message += damage_report
            return message, cover_penetrated

        firemode_mod = 0
        firemode_msg = ""

        if bodypart != "random":
            if "{} severed".format(bodypart) in target.notes :
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

                if firemode == "b" and difficulty <= 20:
                    firemode_mod = 3
                    firemode_msg = " + 3 (burst fire)"
                elif firemode == "f":
                    if burst_size > self.weapons[self.current_weapon]["mag"]:
                        message += "Not enough ammo in magazine (have {})\n".format(self.weapons[self.current_weapon]["mag"])
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
                    .format(self.GetStatValue("REF"), weapontype, self.GetSkillLevel(weapontype), WEAPONS[self.current_weapon]["WA"], diceroll, firemode_msg)

                if cm != 0:
                    message += " + custom_mod({})".format(cm)

                if bodypart != "random":
                    bodypart_mod = -4
                    message += " - bodypart(4)"
                else:
                    bodypart_mod = 0
                    bodypart = rollBodypart()
                    while "{} severed".format(bodypart) in target.notes:
                        bodypart = rollBodypart()

                result = self.GetStatValue("REF") + self.GetSkillLevel(weapontype) + diceroll + WEAPONS[self.current_weapon]["WA"] + bodypart_mod + firemode_mod + cm
                message += " = {}\n".format(result)

                if result >= difficulty:

                    if firemode == "s":
                        damage_report, _ = MakeAShot(target, cover, bodypart, ammo_type)
                        message += damage_report
                        self.weapons[self.current_weapon]["mag"] -= 1

                    elif firemode == "b":
                        hit_count = dice(3)
                        damage_report, cover_penetrated = MakeAShot(target, cover, bodypart, ammo_type)
                        message += damage_report
                        if cover_penetrated:
                            cover -= 1
                        hit_count -= 1
                        message += "{} more hits in 3-round burst\n".format(hit_count)
                        for _ in range(0, hit_count):
                            damage_report, cover_penetrated = MakeAShot(target, cover, "random", ammo_type)
                            message += damage_report
                            if cover_penetrated and cover > 0:
                                cover -= 1
                        self.weapons[self.current_weapon]["mag"] -= 3

                    elif firemode == "f":
                        hit_count = result - difficulty + 1
                        if hit_count > burst_size:
                            hit_count = burst_size
                        message += "{} hits in full auto burst\n".format(hit_count)
                        for _ in range(0, hit_count):
                            damage_report, cover_penetrated = MakeAShot(target, cover, "random", ammo_type)
                            message += damage_report
                            if cover_penetrated and cover > 0:
                                cover -= 1
                        self.weapons[self.current_weapon]["mag"] -= burst_size

                else:
                    message += "Missed\n"
                    self.weapons[self.current_weapon]["mag"] -= burst_size

                message += "Rounds left in mag: {}\n".format(self.weapons[self.current_weapon]["mag"])
            return message

    # end of Character class