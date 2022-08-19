import json
from collections import defaultdict


def ForJSONFile(srcFile, dstFile=None):
    with open(srcFile, 'r', encoding='utf-8') as f:
        originData = json.load(f)
    
    newData = defaultdict(list)

    for data in originData["joint"].values():
        newData["joint"].append(data)
    
    for jointID, vector in originData["force"].items():
        newData["force"].append([int(jointID), vector])

    for data in originData["member"].values():
        newData["member"].append(data)
    
    if "displace" in originData:
        for jointID, vector in originData["displace"].items():
            newData["displace"].append([int(jointID), vector])
    
    if "external" in originData:
        for jointID, vector in originData["external"].items():
            newData["external"].append([int(jointID), vector])
    
    if "internal" in originData:
        for memberID, force in originData["internal"].items():
            newData["internal"].append([int(memberID), force])
    
    if "weight" in originData:
        newData["weight"] = originData["weight"]
    
    if dstFile is not None:
        with open(dstFile, 'w', encoding='utf-8') as f:
            json.dump(newData, f)
    
    return newData