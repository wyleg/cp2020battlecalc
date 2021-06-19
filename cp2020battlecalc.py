#!/usr/bin/python3

import json, os, re, sys

from character import Character

def getCurrentRound():
    rounds = os.listdir("rounds")
    rounds.remove("readme.txt")
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
    print("Round {}\nInitiative order:".format(cur_round))
    init_dict = {}
    for char_name in charlist:
        char = charlist[char_name]
        init_dict.update( { char_name: char.initiative } )
    
    for i in sorted(init_dict, key=init_dict.get, reverse=True):
        char: Character = charlist[i]
        print("{} - {} ({}, {} HP)".format(init_dict[i], char.name, char.state, char.hp))

def makeNextRound():
    def copy_file(src, dest):
        with open(src, "r") as src_file:
            content = src_file.read()
        dest_file =  open(dest, "w")
        dest_file.write(content)
        dest_file.close()
        
    next_round = cur_round + 1
    os.mkdir("rounds/"+str(next_round))
    prev_round_chars = os.listdir("rounds/"+str(cur_round))
    for char in prev_round_chars:
        with open("rounds/{}/{}".format(cur_round, char), "r") as charsheet_file:
            charsheet = json.loads(charsheet_file.read())
            if charsheet["state"] != "dead":
                copy_file("rounds/{}/{}.json".format(cur_round, char),"rounds/{}/{}.json".format(next_round, char))
    print("Started new round {}".format(next_round))

def shootParseArgs(arg_list):
    cover=""
    if arg_list[0] in list(charlist):
        character: Character = charlist[arg_list[0]]
    else:
        print("No such character in this round")
        return
    if arg_list[1] in list(charlist):
        target: Character = charlist[arg_list[1]]
    else:
        print("No such target in this round")
        return
    distance = int(arg_list[2])
    preroll = 0
    nosaveroll = False
    firemode = "s"
    bodypart = "random"
    burst_size = 1
    cm = 0    # custom modifier
    for arg in arg_list:
        if re.match("^pr=.*", arg):
            preroll = int(re.sub("pr=","",arg))
        elif re.match("^cm=.*", arg):
            cm = int(re.sub("cm=","",arg))
        elif arg == "ns" or arg == "nosaveroll":
            nosaveroll = True
        elif re.match("^f=.*", arg):
            firemode = "f"
            burst_size = int(re.sub("f=","",arg))
        elif arg == "b":
            firemode = "b"
            burst_size = 3
        elif re.match("^bp=.*", arg):
            bodypart = re.sub("bp=","",arg)
        elif re.match("^cvr=.*", arg):
            cover = int(re.sub("cvr=","",arg))
    print(character.Shoot(target, distance, burst_size, firemode, cover, preroll, bodypart, cm, nosaveroll))
    
    save_results = input("Write results? y/n: ")
    if save_results == "y":
        writeData()

def writeData():
    for char in list(charlist):
        char_dict = writeCharDataToDict(char)
        with open("rounds/{}/{}.json".format(cur_round, char), "w") as char_file:
            char_file.write(json.dumps(char_dict, indent=3))
    print("Round {} data saved".format(cur_round))

def writeCharDataToDict(char_name):
    character: Character = charlist[char_name]
    return character.__dict__

def calculateInitiative(overwrite=False):
    global charlist
    for char_name in list(charlist):
        char: Character = charlist[char_name]
        if ( char.initiative == 0 or overwrite ) and char.state != "dead":
            char.RollInitiative()
    writeData()

def skillcheck(arg_list):
    if arg_list[0] in list(charlist):
        character: Character = charlist[arg_list[0]]
    else:
        print("No such character in this round")
        return
    skill = arg_list[1]
    difficulty = int(arg_list[2])
    cm =0
    for arg in arg_list:
        if re.match("^pr=.*", arg):
            preroll = int(re.sub("pr=","",arg))
        elif re.match("^cm=.*", arg):
            cm = int(re.sub("cm=","",arg))
    _, report = character.SkillCheck(skill, difficulty, cm)
    print(report)


charlist = {}

cur_round = getCurrentRound()
loadRoundData(cur_round)

def print_help():
    print("\nCyberpunk 2020 Battle Calculator v1.0.0\n  author: wyleg\n\nCommands:\n\
    getroundinfo\n\
    getcharinfo <character>\n\
    nextround\n\
    calcinit [ow]\n\
    shoot <character> <target> <distance> [preroll=<number>] [ns|nosaveroll] [cm=<modifier>] [f=<fullauto_burst_size>|b|s] [bp=<bodypart>] [cvr=<cover_sp>]\n\
    skillcheck <character> <skill> <difficulty> [cm=<custom modifier>]\n")

def executeCommand(args):
    cmd = args[0]
    args_list = args
    args_list.pop(0)
    if cmd == "exit":
        sys.exit(0)
    if cmd == "help":
        print_help()
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
        getRoundInfo()
    elif cmd == "skillcheck":
        skillcheck(args_list)

if len(sys.argv) > 1:
    args_list = list(sys.argv)
    args_list.pop(0)
    executeCommand(args_list)
else:
    print_help()