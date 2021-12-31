import random
import math
from .truss import Truss
from .type  import MemberType
from .utils import OnlyOneMemberTypeError, MinStressTooLargeError, MinDisplaceTooLargeError


INF = float("inf")


def _InfinteLoop():
    i = 0
    while True:
        yield i
        i += 1


class GA:
    def __init__(self, truss: Truss, memberTypeList: list[MemberType], allowStress=30000, allowDisplace=10, 
                       penaltyInternal=1e5, penaltyDisplace=1e5, nIteration=None, nPatience=50, nPop=200, nElite=50, 
                       pCrossover=0.7, pMutate=0.1, pOrigin=0.1, isWeightedInit=False):
        # Population settings:
        self.nPop           = nPop
        self.nElite         = nElite
        self.pCrossover     = pCrossover
        self.pMutate        = pMutate
        self.pOrigin        = pOrigin
        self.pRandomGene    = 1. - pCrossover - pMutate - pOrigin
        self.isWeightedInit = isWeightedInit

        # Fitness function settings:
        self.nIteration     = nIteration
        self.nPatience      = nPatience
        self.penaltyInt     = penaltyInternal
        self.penaltyDis     = penaltyDisplace

        # Truss settings:
        self.truss          = truss
        self.allowStress    = allowStress
        self.allowDisplace  = allowDisplace
        self.typeList       = memberTypeList
        self.nMember        = self.truss.nMember
        self.nType          = len(memberTypeList)
        self.memberIDList   = self.truss.GetMemberIDs()
        self.memberIDMap    = {typeID: memberID for typeID, memberID in enumerate(self.memberIDList)}

        # Rationality:
        self.CheckRatioality()
    
    def CheckRatioality(self):
        truss, allowStress, allowDisplace  = self.truss, self.allowStress, self.allowDisplace

        # Check sum of probabilties must <= 1.0:
        if self.pCrossover + self.pMutate + self.pOrigin > 1.:
            raise ValueError(f"pCrossover + pMutate + pOrigin must <= 1.0, but got [{self.pCrossover + self.pMutate + self.pOrigin :.4f}].")

        # Check whether number of member types >= 2 or not:
        if self.nType <= 1:
            raise OnlyOneMemberTypeError(f"Number of member types must >= 2, but got {self.nType}.")
        
        # Get member types which have max [A] value and max [E*A] value, repectively.
        maxA, maxEA, maxAType, maxEAType = -INF, -INF, None, None
        for memberType in self.typeList:
            a, ea = memberType.a, memberType.e * memberType.a
            if a  > maxA : maxA , maxAType  = a , memberType
            if ea > maxEA: maxEA, maxEAType = ea, memberType

        # Check whether minimum stress is smaller than allowable stress:
        for memberID in self.memberIDList:
            truss.SetMemberType(memberID, maxAType)

        truss.Solve()
        if not truss.IsInternalStressAllowed(allowStress)[0]:
            raise MinStressTooLargeError("Minimum stress is too large. Need other member types which have more [A] value.")

        # Check whether minimum displacement is smaller than allowable displacement:
        for memberID in self.memberIDList:
            truss.SetMemberType(memberID, maxEAType)

        truss.Solve()
        if not truss.IsDisplacementAllowed(allowDisplace)[0]:
            raise MinDisplaceTooLargeError("Minimum displacement is too large. Need other member types which have more [E*A] value.")
    
    def GetBestFeasibleGene(self, pop):
        minFitness, minGene, isMinInternalAllowed, isMinDisplaceAllowed = INF, None, False, False
        for gene in pop:
            fitness, isInternalAllowed, isDisplaceAllowed = self.GetFitness(gene)
            if isInternalAllowed and isDisplaceAllowed and fitness < minFitness:
                minFitness, minGene, isMinInternalAllowed, isMinDisplaceAllowed = fitness, gene, isInternalAllowed, isDisplaceAllowed
        
        return minGene, (minFitness, isMinInternalAllowed, isMinDisplaceAllowed)

    def TranslateGene(self, gene):
        memberIDMap, typeList = self.memberIDMap, self.typeList
        return {memberIDMap[i]: typeList[locus] for i, locus in enumerate(gene)}
    
    def GetFitness(self, gene):
        truss, memberIDMap, typeList = self.truss, self.memberIDMap, self.typeList
        for i, locus in enumerate(gene):
            truss.SetMemberType(memberIDMap[i], typeList[locus])

        truss.Solve()
        isInternalAllowed, internalViolation = truss.IsInternalStressAllowed(self.allowStress, True)
        isDisplaceAllowed, displaceViolation = truss.IsDisplacementAllowed(self.allowDisplace, True)

        fitness = truss.weight
        if not isInternalAllowed: fitness += internalViolation / self.allowStress   * self.penaltyInt
        if not isDisplaceAllowed: fitness += displaceViolation / self.allowDisplace * self.penaltyDis
        return fitness, isInternalAllowed, isDisplaceAllowed
    
    def GetRandomGene(self):
        return random.choices(range(self.nType), k=self.nMember)
    
    def Initialize(self):
        nType, nMember, typeChosenProbs = self.nType, self.nMember, [math.exp(t.a) for t in self.typeList] if self.isWeightedInit else None
        return [random.choices(range(nType), k=nMember, weights=typeChosenProbs) for _ in range(self.nPop)]
    
    def Select(self, pop):
        pop = sorted([[gene, self.GetFitness(gene)] for gene in pop], key=lambda x: x[1][0])
        elitePop = [gene for gene, _ in pop[:self.nElite]]
        return elitePop, len(elitePop), pop[0][1]
    
    def Crossover(self, gene0, gene1):
        cut0, cut1 = random.sample(range(self.nMember), k=2)
        cut0, cut1 = (cut0, cut1) if cut0 <= cut1 else (cut1, cut0)
        return [gene0[i] if i < cut0 or i >= cut1 else gene1[i] for i in range(self.nMember)]

    def Mutate(self, gene):
        gene = gene.copy()
        mutateIndex = random.randint(0, self.nMember - 1)
        gene[mutateIndex] = random.choice([typeID for typeID in range(self.nType) if typeID != gene[mutateIndex]])
        return gene

    def Evolve(self, isPrintMessage=True):
        # Initialize:
        pop, nPop = self.Initialize(), self.nPop
        pCrossover, pMutate, pOrigin   = self.pCrossover, self.pCrossover + self.pMutate, self.pCrossover + self.pMutate + self.pOrigin
        nIteration, nPatience = self.nIteration, self.nPatience

        # Evolution loops:
        bestFitness, bestFitnessHistory, nWaitBestIter, isEarlyStopping = INF, [], 0, False
        for i in (range(nIteration) if nIteration is not None else _InfinteLoop()):
            
            # Select elites:
            elitePop, nElite, (minFitness, isInternalAllowed, isDisplaceAllowed) = self.Select(pop)
            newPop = [None for _ in range(nPop)]
            newPop[:nElite] = elitePop

            # Early stopping:
            if minFitness < bestFitness:
                bestFitness, nWaitBestIter = minFitness, 0
            else:
                nWaitBestIter += 1
                if nWaitBestIter >= nPatience:
                    isEarlyStopping = True
                    break
            
            bestFitnessHistory.append(bestFitness)

            # Print meaasge of this iteration:
            if isPrintMessage:
                print(f"\rIteration: {i :6d}, nWaitBestIter: {nWaitBestIter :3d}, minFitness: {minFitness :12.4f}, isInternalAllowed: {str(isInternalAllowed) :5s}, isDisplaceAllowed: {str(isDisplaceAllowed) :5s}", end='')

            # Crossover or mutate or do nothing:
            for j in range(nElite, nPop):
                p = random.random()
                if p <= pCrossover:
                    newPop[j] = self.Crossover(*random.sample(elitePop, k=2))
                elif pCrossover < p <= pMutate:
                    newPop[j] = self.Mutate(random.choice(elitePop))
                elif pMutate < p <= pOrigin:
                    newPop[j] = pop[j]
                else:
                    newPop[j] = self.GetRandomGene()
            
            pop = newPop
        
        # Print and output the final result:
        minGene, minGeneInfo = self.GetBestFeasibleGene(pop)
        if isPrintMessage:
            print(f"\rIteration: {i + 1 :6d}, nWaitBestIter: {nWaitBestIter :3d}, minFitness: {minFitness :10.4f}, isInternalAllowed: {str(isInternalAllowed) :5s}, isDisplaceAllowed: {str(isDisplaceAllowed) :5s} {'...EarlyStopping !' if isEarlyStopping else ''}")
        
        return minGene, minGeneInfo, pop, bestFitnessHistory