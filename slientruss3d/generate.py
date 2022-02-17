import os
import random


from .truss import Truss
from .plot  import TrussPlotter
from .type  import MemberType
from .utils import GetPowerset, TrussNotStableError


class LinkType:
    LeftBottom_RightTop = 0
    RightBottom_LeftTop = 1
    Cross               = 2
    Random              = 3


class GenerateMethod:
    DFS    = 0
    BFS    = 1
    Random = 2


class CubeTruss:
    def __init__(self, coordinate, usedDict={}):
        self.__coord = coordinate
        self.__links = []
        self.jointIDs = [None for _ in range(8)]
        self.GenerateNew(usedDict)

    def __repr__(self):
        return str(self.jointIDs)
    
    def __getitem__(self, i):
        return self.jointIDs[i]
    
    def __setitem__(self, i, val):
        self.jointIDs[i] = val
    
    def GetCubeVertices(self):
        dim = len(self.__coord)
        vertices = []
        for indexes in GetPowerset(list(range(dim))):
            joint = tuple([(v + 1 if i in indexes else v) for i, v in enumerate(self.__coord)])
            vertices.append(joint)
        
        return vertices
    
    def GenerateNew(self, usedDict={}):
        vertices, maxJointID = self.GetCubeVertices(), max(usedDict.values()) if usedDict.values() else -1
        for i, joint in enumerate(vertices):
            if joint in usedDict:
                self[i] = usedDict[joint]
            else:
                maxJointID += 1
                self[i]          = maxJointID
                usedDict[joint] = maxJointID
    
    def LinkMember(self, linkType=LinkType.Random):

        def SampleLink(links, choices, linkType):
            choice = choices[random.sample(range(len(choices)), k=1)[0]] if linkType == LinkType.Random else choices[linkType]
            if list(filter(lambda x: hasattr(x, '__iter__'), choice)):
                links.extend(choice)
            else:
                links.append(choice)

        links = self.__links
        links.clear()

        # Middle:
        SampleLink(links, ([self[0], self[5]], [self[1], self[4]], [[self[0], self[5]], [self[1], self[4]]]), linkType)
        SampleLink(links, ([self[1], self[7]], [self[3], self[5]], [[self[1], self[7]], [self[3], self[5]]]), linkType)
        SampleLink(links, ([self[3], self[6]], [self[2], self[7]], [[self[3], self[6]], [self[2], self[7]]]), linkType)
        SampleLink(links, ([self[2], self[4]], [self[0], self[6]], [[self[2], self[4]], [self[0], self[6]]]), linkType)
        SampleLink(links, ([self[4], self[7]], [self[5], self[6]], [[self[4], self[7]], [self[5], self[6]]]), linkType)
        SampleLink(links, ([self[0], self[3]], [self[1], self[2]], [[self[0], self[3]], [self[1], self[2]]]), linkType)

        # Top cycle:
        links.append([self[4], self[5]])
        links.append([self[5], self[7]])
        links.append([self[6], self[7]])
        links.append([self[4], self[6]])

        # Bottom cycle:
        links.append([self[0], self[1]])
        links.append([self[0], self[2]])
        links.append([self[1], self[3]])
        links.append([self[2], self[3]])

        # Side cycle:
        links.append([self[0], self[4]])
        links.append([self[1], self[5]])
        links.append([self[2], self[6]])
        links.append([self[3], self[7]])

        return links


class CubeGrid:
    def __init__(self, xMax, yMax, zMax):
        self.__xMax = xMax
        self.__yMax = yMax
        self.__zMax = zMax
        self.__usedDict = {}
        self.grid = [[[False for _ in range(zMax)] for _ in range(yMax)] for _ in range(xMax)]
    
    def __getitem__(self, coordinate):
        return self.grid[coordinate[0]][coordinate[1]][coordinate[2]]
    
    def __setitem__(self, coordinate, isUsed):
        self.grid[coordinate[0]][coordinate[1]][coordinate[2]] = isUsed
    
    def IsOutOfRange(self, coordinate):
        return ( coordinate[0] >= self.__xMax or coordinate[0] < 0 or
                 coordinate[1] >= self.__yMax or coordinate[1] < 0 or
                 coordinate[2] >= self.__zMax or coordinate[2] < 0 )
    
    def GetRandomFeasible(self):
        return random.choice([(x, y, z) for z in range(self.__zMax) for y in range(self.__yMax) for x in range(self.__xMax) if not self[(x, y, z)]])
    
    def GetNextFeasibles(self, coordinate, isSuffle=True):
        nextCoords = []
        for nextDirect in ((-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)):
            nextCoord = tuple(v0 + v1 for v0, v1 in zip(coordinate, nextDirect))
            if not self.IsOutOfRange(nextCoord) and not self[nextCoord]:
                nextCoords.append(nextCoord)
        
        if isSuffle: random.shuffle(nextCoords)
        return nextCoords
    
    def RandomGenerateCubes(self, numCube=None, method=GenerateMethod.DFS):
        numCube = random.randint(1, self.__xMax * self.__yMax * self.__zMax) if numCube is None else numCube
        self.__usedDict.clear()

        usedDict, cubes, coords = self.__usedDict, [], [self.GetRandomFeasible()]
        while len(cubes) < numCube and coords:
            if method == GenerateMethod.DFS:
                coord = coords.pop()
            elif method == GenerateMethod.BFS:
                coord = coords.pop(0)
            elif method == GenerateMethod.Random:
                if random.random() <= 0.5:
                    coord = coords.pop()
                else:
                    coord = coords.pop(0)

            self[coord] = True
            coords.extend([newCoord for newCoord in self.GetNextFeasibles(coord) if newCoord not in coords])
            cubes.append(CubeTruss(coord, usedDict))
        
        return cubes
    
    def ProcessPinSupport(self, isAddPinSupport, length):
        minZ = float("inf")
        for _, _, z in self.__usedDict:
            if z < minZ: minZ = z
        
        length = [float(v) for v in length]
        return {jointID: [[float(x * length[0]), float(y * length[1]), float((z - minZ) * length[2])], 
                          ("PIN" if z == minZ else "NO") if isAddPinSupport else "NO"] 
                for (x, y, z), jointID in self.__usedDict.items()}
    
    def CubesToTruss(self, cubes, length=(100., 100., 100.), isAddPinSupport=True, linkType=LinkType.Random, memberType=[1., 1e7, 0.1]):
        # Joints:
        joints = self.ProcessPinSupport(isAddPinSupport, length)

        # Members:
        members = []
        for cube in cubes:
            links = cube.LinkMember(linkType)
            members.extend([[link, memberType] for link in links])
        
        members = {i: member for i, member in enumerate(members)}

        # Serialize:
        return {'joint': joints, 'force': {}, 'member': members}


def GenerateRandomCubeTrusses(gridRange=(5, 5, 5), numCubeRange=(5, 5), numEachRange=(1, 10), lengthRange=(50, 150), forceRange=[(-30000, 30000), (-30000, 30000), (-30000, 30000)], 
                              nForceRange=None, method=GenerateMethod.Random, linkType=LinkType.Random, memberTypes=[[1., 1e7, 0.1]], isAddPinSupport=True, isDoStructuralAnalysis=False, 
                              isPlotTruss=False, isPrintMessage=True, saveFolder=None):
    
    def AssignRandomForces(trussData, forceRange, nForceRange):
        notSupportJoints = [jointID for jointID, (_, supportType) in trussData['joint'].items() if supportType == "NO"]
        if nForceRange is None:
            nForce = random.randint(1, len(notSupportJoints))
        else:
            nForce = random.randint(1                     if nForceRange[0] is None else nForceRange[0], 
                                    len(notSupportJoints) if nForceRange[1] is None else nForceRange[1])

        trussData['force'] = {jointID: [random.uniform(*forceRange[i]) for i in range(3)] 
                              for jointID in random.sample(notSupportJoints, nForce)}
        return trussData
    
    def AssignRandomMemberType(trussData, memberTypes):
        memberDict = trussData['member']
        for memberID in memberDict:
            choice = random.choice(memberTypes)
            memberDict[memberID][1] = choice.Serialize() if isinstance(choice, MemberType) else choice
        
        return trussData

    trussList = []
    for numCube in range(numCubeRange[0], numCubeRange[1] + 1):
        for i in range(numEachRange[0], numEachRange[1] + 1):
            while True:
                try:
                    if isPrintMessage: 
                        print(f"\rnumCube : {numCube :5d}, i : {i :5d}", end='')

                    cubeGrid  = CubeGrid(*gridRange)
                    cubes     = cubeGrid.RandomGenerateCubes(numCube, method)
                    trussData = cubeGrid.CubesToTruss(cubes, [random.uniform(*lengthRange) for _ in range(3)], isAddPinSupport, linkType)
                    AssignRandomForces(trussData, forceRange, nForceRange)
                    AssignRandomMemberType(trussData, memberTypes)
                    truss = Truss(3).LoadFromJSON(data=trussData)

                    if isDoStructuralAnalysis:
                        truss.Solve()

                    if saveFolder is not None:
                        truss.DumpIntoJSON(os.path.join(saveFolder, f"cube-{numCube}_ga_{i}.json"))

                    if isPlotTruss:
                        TrussPlotter(truss, 
                                     maxScaledDisplace=lengthRange[1] * 0.1,
                                     maxScaledForce=lengthRange[1] * 0.6, 
                                     isEqualAxis=True).Plot(isSave=True, 
                                                            savePath=os.path.join(saveFolder, f"cube-{numCube}_plot_{i}.png"))
                    trussList.append(truss)
                    break

                except TrussNotStableError:
                    if isPrintMessage: print("\nTruss is not stable. Re-genrating...\n")

    return trussList