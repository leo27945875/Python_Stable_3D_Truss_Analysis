import os
import json
import random
from math import ceil

from .truss import Truss
from .plot  import TrussPlotter
from .type  import MemberType, LinkType, GenerateMethod
from .utils import GetPowerset, TrussNotStableError, PinNotEnoughError


# For data augmentation:
class TrussDataAugmenter:
    @staticmethod
    def IsTrussClass(trussData):
        isTrussClass = isinstance(trussData, Truss)
        if isTrussClass:
            return isTrussClass, trussData.Serialize()
        
        return isTrussClass, trussData
    
    @staticmethod
    def GetCentroid(jointDict):
        n, sumXYZ = len(jointDict), [0., 0., 0.]
        for jointData in jointDict:
            sumXYZ[:] = [sumXYZ[i] + jointData[0][i] for i in range(3)]
        
        return [x / n for x in sumXYZ]
    
    @staticmethod
    def GetStableMinNumPin(trussData):
        return ceil((len(trussData['joint']) * 3 - len(trussData['member'])) / 3)


class NoChange(TrussDataAugmenter):
    """
    Do nothing to the truss.
    """
    def __call__(self, trussData):
        return trussData


class AddJointNoise(TrussDataAugmenter):
    """
    Add guassian noise to all positions of the joints.
    """
    def __init__(self, noiseMeans=[0., 0., 0.], noiseStds=[1., 1., 1.]):
        self.noiseMeans = noiseMeans
        self.noiseStds  = noiseStds
    
    def __call__(self, trussData):
        isTrussClass, _trussData = self.IsTrussClass(trussData)
        jointDict = _trussData['joint']
        for jointData in jointDict:
            jointData[0][:] = [jointData[0][i] + random.gauss(self.noiseMeans[i], self.noiseStds[i]) for i in range(3)]
        
        if isTrussClass:
            trussData.LoadFromJSON(data=_trussData, isOutputFile=trussData.isSolved)
        
        return trussData


class MoveToCentroid(TrussDataAugmenter):
    """
    Move the centroid of the truss to [0., 0., 0.].
    """
    def __call__(self, trussData):
        isTrussClass, _trussData = self.IsTrussClass(trussData)
        jointDict = _trussData['joint']
        centroid  = self.GetCentroid(jointDict)
        for jointData in jointDict:
            jointData[0][:] = [jointData[0][i] - centroid[i] for i in range(3)]
        
        if isTrussClass:
            trussData.LoadFromJSON(data=_trussData, isOutputFile=trussData.isSolved)
        
        return trussData


class Translation(TrussDataAugmenter):
    """
    Translate the whole truss.
    """
    def __init__(self, translation):
        self.translation = translation
    
    def __call__(self, trussData):
        isTrussClass, _trussData = self.IsTrussClass(trussData)

        translation = self.translation
        for jointData in _trussData['joint']:
            jointData[0][:] = [jointData[0][i] + translation[i] for i in range(3)]
        
        if isTrussClass:
            trussData.LoadFromJSON(data=_trussData, isOutputFile=trussData.isSolved)
        
        return trussData


class RandomTranslation(TrussDataAugmenter):
    """
    Translate the whole truss randomly.
    """
    def __init__(self, translateRange=[-1., 1.]):
        self.translateRange = translateRange

    def __call__(self, trussData):
        translation = [random.uniform(*self.translateRange) for _ in range(3)]
        return Translation(translation)(trussData)


class RandomResetPin(TrussDataAugmenter):
    """
    Reset the positions and number of pin supports. (Max number of pin supports = [Number of joints in the truss] * maxNumPinRatio)
    """
    def __init__(self, minNumPin=3, maxNumPinRatio=None):
        if minNumPin < 3:
            raise PinNotEnoughError("Number of pins must >= 3.")

        self.minNumPin      = minNumPin
        self.maxNumPinRatio = maxNumPinRatio
    
    def __call__(self, trussData):
        isTrussClass, _trussData = self.IsTrussClass(trussData)
        jointData = _trussData['joint']
        minNumPin = self.GetStableMinNumPin(_trussData) if self.minNumPin is None else max(self.minNumPin, self.GetStableMinNumPin(_trussData))
        maxNumPin = len(jointData) if self.maxNumPinRatio is None else int(self.maxNumPinRatio * len(jointData))
        sampledJointIDs = set(random.sample(range(len(jointData)), k=random.choice(range(minNumPin, maxNumPin + 1))))
        for jointID, jointData in enumerate(jointData):
            if jointID in sampledJointIDs:
                jointData[-1] = "PIN"
            else:
                jointData[-1] = "NO"
        
        if isTrussClass:
            trussData.LoadFromJSON(data=_trussData, isOutputFile=trussData.isSolved)
        
        return trussData

class TrussDataAugmenterList(TrussDataAugmenter):
    def __init__(self, *augmenters):
        self.augmenters = augmenters
    
    def __call__(self, trussData):
        for augmenter in self.augmenters:
            trussData = augmenter(trussData)
        
        return trussData


# Generate cube truss:
class CubeTruss:
    def __init__(self, coordinate, usedDict={}):
        self.__coord = coordinate
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
                self[i]         = maxJointID
                usedDict[joint] = maxJointID
    
    def LinkMember(self, linkType, hasLinked):

        def SampleLink(links, choices, linkType, hasLinked):
            choice = choices[random.sample(range(len(choices)), k=1)[0]] if linkType == LinkType.Random else choices[linkType]
            if list(filter(lambda x: hasattr(x, '__iter__'), choice)):
                if hasLinked is None:
                    links.extend(choice)
                else:
                    for c in choice:
                        if (link := tuple(c)) not in hasLinked:
                            links.append(c)
                            hasLinked.add(link)
            else:
                if hasLinked is None:
                    links.append(choice)
                else:
                    if (link := tuple(choice)) not in hasLinked:
                        links.append(choice)
                        hasLinked.add(link)

        links = []

        # Middle:
        SampleLink(links, ([self[0], self[5]], [self[1], self[4]], [[self[0], self[5]], [self[1], self[4]]]), linkType, hasLinked)
        SampleLink(links, ([self[1], self[7]], [self[3], self[5]], [[self[1], self[7]], [self[3], self[5]]]), linkType, hasLinked)
        SampleLink(links, ([self[3], self[6]], [self[2], self[7]], [[self[3], self[6]], [self[2], self[7]]]), linkType, hasLinked)
        SampleLink(links, ([self[2], self[4]], [self[0], self[6]], [[self[2], self[4]], [self[0], self[6]]]), linkType, hasLinked)
        SampleLink(links, ([self[4], self[7]], [self[5], self[6]], [[self[4], self[7]], [self[5], self[6]]]), linkType, hasLinked)
        SampleLink(links, ([self[0], self[3]], [self[1], self[2]], [[self[0], self[3]], [self[1], self[2]]]), linkType, hasLinked)

        for choice in [
                # Top cycle:
                [self[4], self[5]], [self[5], self[7]], [self[6], self[7]], [self[4], self[6]],
                # Bottom cycle:
                [self[0], self[1]], [self[0], self[2]], [self[1], self[3]], [self[2], self[3]],
                # Side cycle:
                [self[0], self[4]], [self[1], self[5]], [self[2], self[6]], [self[3], self[7]]
        ]:
            if hasLinked is None:
                links.append(choice)
            else:
                if (link := tuple(choice)) not in hasLinked: 
                    links.append(choice)
                    hasLinked.add(link)

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
        joints = [None for _ in self.__usedDict]
        for (x, y, z), jointID in self.__usedDict.items():
            joints[jointID] = [[float(x * length[0]), float(y * length[1]), float((z - minZ) * length[2])], 
                                ("PIN" if z == minZ else "NO") if isAddPinSupport else "NO"] 
        return joints
    
    def CubesToTruss(self, cubes, length, isAddPinSupport=True, isAllowParallel=True, linkType=LinkType.Random, memberType=[1., 1e7, 0.1]):
        # Joints:
        joints = self.ProcessPinSupport(isAddPinSupport, length)

        # Members:
        members, hasLinked = [], None if isAllowParallel else set()
        for cube in cubes:
            links = cube.LinkMember(linkType, hasLinked)
            members.extend([[link, memberType] for link in links])
        
        # Serialize:
        return {'joint': joints, 'force': {}, 'member': members}


def GenerateRandomCubeTrusses(gridRange=(5, 5, 5), numCubeRange=(5, 5), numEachRange=(1, 10), lengthRange=(50, 150), forceRange=[(-30000, 30000), (-30000, 30000), (-30000, 30000)], 
                              nForceRange=None, method=GenerateMethod.Random, linkType=LinkType.Random, memberTypes=[[1., 1e7, 0.1]], isAddPinSupport=True, isAllowParallel=False,
                              isDoStructuralAnalysis=False, isPlotTruss=False, isPrintMessage=True, saveFolder=None, augmenter=NoChange(), seed=None):
    
    def AssignRandomForces(trussData, forceRange, nForceRange):
        notSupportJoints = [jointID for jointID, (_, supportType) in enumerate(trussData['joint']) if supportType == "NO"]
        if nForceRange is None:
            nForce = random.randint(1, len(notSupportJoints))
        else:
            nForce = random.randint(1                     if nForceRange[0] is None else nForceRange[0], 
                                    len(notSupportJoints) if nForceRange[1] is None else nForceRange[1])

        trussData['force'] = [[jointID, [random.uniform(*forceRange[i]) for i in range(3)]]
                              for jointID in sorted(random.sample(notSupportJoints, nForce))]
        return trussData
    
    def AssignRandomMemberType(trussData, memberTypes):
        memberData = trussData['member']
        for memberID in range(len(memberData)):
            choice = random.choice(memberTypes)
            memberData[memberID][1] = choice.Serialize() if isinstance(choice, MemberType) else choice
        
        return trussData

    if seed is not None:
        random.seed(seed)
    
    trussList = []
    for numCube in range(numCubeRange[0], numCubeRange[1] + 1):
        for i in range(numEachRange[0], numEachRange[1] + 1):
            while True:
                try:
                    if isPrintMessage: 
                        print(f"\rnumCube : {numCube :5d}, case : {i :5d}", end='')

                    cubeGrid  = CubeGrid(*gridRange)
                    cubes     = cubeGrid.RandomGenerateCubes(numCube, method)
                    trussData = cubeGrid.CubesToTruss(cubes, [random.uniform(*lengthRange) for _ in range(3)], isAddPinSupport, isAllowParallel, linkType)
                    AssignRandomForces      (trussData, forceRange, nForceRange)
                    AssignRandomMemberType  (trussData, memberTypes)
                    truss = Truss(3).LoadFromJSON(data=augmenter(trussData))

                    if isDoStructuralAnalysis:
                        truss.Solve()
                    else:
                        if not truss.isStable: raise TrussNotStableError

                    if saveFolder is not None:
                        truss.DumpIntoJSON(os.path.join(saveFolder, f"cube-{numCube}_case_{i}.json"))

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