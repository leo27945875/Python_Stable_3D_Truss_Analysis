import random
from .truss import Truss
from .type  import MemberType
from .utils import (EliteNumberTooMuchError, 
                    ProbabilityGreaterThanOneError, 
                    OnlyOneMemberTypeError, 
                    MinStressTooLargeError, 
                    MinDisplaceTooLargeError, 
                    InfinteLoop, INF)


class GA:
    """
    The generic algorithm to optimize a truss by searching the best combination of member types of members in the truss.
    """
    def __init__(
            self, 
            truss           : Truss                     ,
            memberTypeList  : list[MemberType]          ,
            allowStress     : float            = 30000. ,
            allowDisplace   : float            = 10.    ,
            nIteration      : int              = None   ,
            nPatience       : int              = 50     ,
            nPop            : int              = 200    ,
            nElite          : int              = 50     ,
            pCrossover      : float            = 0.7    ,
            pMutate         : float            = 0.1    ,
            pOrigin         : float            = 0.1    ,
            isCheckWorst    : bool             = False
        ):
        # Population settings:
        self.nPop          = nPop
        self.nElite        = nElite
        self.pCrossover    = pCrossover
        self.pMutate       = pMutate
        self.pOrigin       = pOrigin
        self.pRandomGene   = 1. - pCrossover - pMutate - pOrigin

        # Iteration policy settings:
        self.nIteration    = nIteration
        self.nPatience     = nPatience

        # Truss settings:
        self.truss         = truss
        self.allowStress   = allowStress
        self.allowDisplace = allowDisplace
        self.typeList      = memberTypeList
        self.nMember       = self.truss.nMember
        self.nType         = len(memberTypeList)
        self.memberIDList  = self.truss.GetMemberIDs()
        self.memberIDMap   = {typeID: memberID for typeID, memberID in enumerate(self.memberIDList)}

        # Feasible record:
        self.__lastFeasibleGene    = [None for _ in range(self.nMember)]
        self.__lastFeasibleFitness = None

        # Rationality:
        self.CheckRatioality(isCheckWorst)

    @property
    def memberTypeWeightedInitProb(self):
        return [1. for _ in self.typeList]
    
    def _RecordFeasible(self, evaluatedPop, isSorted=False):
        for gene, (fitness, isInternalAllowed, isDisplaceAllowed) in evaluatedPop:
            if isInternalAllowed and isDisplaceAllowed and (self.__lastFeasibleFitness is None or fitness < self.__lastFeasibleFitness):
                self.__lastFeasibleGene[:], self.__lastFeasibleFitness = gene, fitness
                if isSorted: break

    def CheckRatioality(self, isCheckWorst):
        truss, allowStress, allowDisplace  = self.truss, self.allowStress, self.allowDisplace

        # Chech whether number of elites <= number of population:
        if self.nElite > self.nPop:
            raise EliteNumberTooMuchError(f"Number of elites must <= number of population. Got [nElite] = {self.nElite}, [nPop] = {self.nPop}.")

        # Check sum of probabilties must <= 1.0:
        if self.pCrossover + self.pMutate + self.pOrigin > 1.:
            raise ProbabilityGreaterThanOneError(f"[pCrossover] + [pMutate] + [pOrigin] must <= 1.0, but got [{self.pCrossover + self.pMutate + self.pOrigin :.4f}].")

        # Check whether number of member types >= 2 or not:
        if self.nType <= 1:
            raise OnlyOneMemberTypeError(f"Number of member types must >= 2, but got {self.nType}.")
        
        # Check whether minmum stress and strain are both lower than allowable values:
        if isCheckWorst:
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
    
    def GetBestFeasibleGene(self, pop, isDirectlyReturnRecord=False):
        if isDirectlyReturnRecord and self.__lastFeasibleFitness is not None:
            return self.__lastFeasibleGene, (self.__lastFeasibleFitness, True, True)

        minFitness, minGene, isMinInternalAllowed, isMinDisplaceAllowed = INF, None, False, False
        for gene in pop:
            fitness, isInternalAllowed, isDisplaceAllowed = self.GetFitness(gene)
            if isInternalAllowed and isDisplaceAllowed and fitness < minFitness:
                minFitness, minGene, isMinInternalAllowed, isMinDisplaceAllowed = fitness, gene, isInternalAllowed, isDisplaceAllowed
        
        if minGene is None and self.__lastFeasibleFitness is not None:
            return self.__lastFeasibleGene, (self.__lastFeasibleFitness, True, True)
        
        return minGene, (minFitness, isMinInternalAllowed, isMinDisplaceAllowed)

    def TranslateGene(self, gene):
        memberIDMap, typeList = self.memberIDMap, self.typeList
        return {memberIDMap[i]: typeList[locus] for i, locus in enumerate(gene)}
    
    def GetRandomGene(self):
        return random.choices(range(self.nType), k=self.nMember)
    
    def SetMemberTypesByGene(self, gene, truss):
        memberIDMap, typeList = self.memberIDMap, self.typeList
        for i, locus in enumerate(gene):
            truss.SetMemberType(memberIDMap[i], typeList[locus])
        
        return truss
    
    def GetFitness(self, gene):
        truss = self.SetMemberTypesByGene(gene, self.truss)
        truss.Solve()

        isInternalAllowed, internalViolation = truss.IsInternalStressAllowed(self.allowStress, True)
        isDisplaceAllowed, displaceViolation = truss.IsDisplacementAllowed(self.allowDisplace, True)

        fitness = truss.weight
        if not isInternalAllowed: fitness += internalViolation / self.allowStress   * 1e5
        if not isDisplaceAllowed: fitness += displaceViolation / self.allowDisplace * 1e5
        return fitness, isInternalAllowed, isDisplaceAllowed
    
    def Initialize(self):
        nType, nMember, typeChosenProbs = self.nType, self.nMember, self.memberTypeWeightedInitProb
        return [random.choices(range(nType), k=nMember, weights=typeChosenProbs) for _ in range(self.nPop)]
    
    def Select(self, pop, isRecordFeasible=False):
        fitnessFunc = self.GetFitness
        pop      = sorted([[gene, fitnessFunc(gene)] for gene in pop], key=lambda x: x[1][0])
        elitePop = [gene for gene, _ in pop[:self.nElite]]
        if isRecordFeasible: self._RecordFeasible(pop, isSorted=True)
        return elitePop, pop[0][1]
    
    def Crossover(self, gene0, gene1):
        cut0, cut1 = random.sample(range(self.nMember), k=2)
        cut0, cut1 = (cut0, cut1) if cut0 <= cut1 else (cut1, cut0)
        return [gene0[i] if i < cut0 or i >= cut1 else gene1[i] for i in range(self.nMember)]

    def Mutate(self, gene):
        gene = gene.copy()
        mutateIndex = random.randint(0, self.nMember - 1)
        gene[mutateIndex] = random.choice([typeID for typeID in range(self.nType) if typeID != gene[mutateIndex]])
        return gene

    def UpdatePop(self, pop, elitePop):
        nPop      , nElite           = self.nPop      , self.nElite
        pCrossover, pMutate, pOrigin = self.pCrossover, self.pCrossover + self.pMutate, self.pCrossover + self.pMutate + self.pOrigin
        
        newPop = [None for _ in range(nPop)]
        newPop[:nElite] = elitePop
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
        
        return newPop
    
    def Evolve(self, isPrintMessage=True):
        nIteration, nPatience = self.nIteration, self.nPatience

        # Initialize:
        pop = self.Initialize()

        # Evolution loops:
        bestFitness, bestFitnessHistory, nWaitBestIter, isEarlyStopping = INF, [], 0, False
        for i in (range(nIteration) if nIteration is not None else InfinteLoop()):
            
            # Select elites:
            elitePop, (minFitness, isInternalAllowed, isDisplaceAllowed) = self.Select(pop, True)

            # Early stopping:
            if minFitness < bestFitness:
                bestFitness, nWaitBestIter = minFitness, 0
            else:
                nWaitBestIter += 1
                if nWaitBestIter >= nPatience:
                    isEarlyStopping = True
                    break
            
            # Record the best fitness of this iteration:
            bestFitnessHistory.append(bestFitness)

            # Print meaasge of this iteration:
            if isPrintMessage:
                print(f"\rIteration: {i :6d}, nWaitBestIter: {nWaitBestIter :3d}, minFitness: {minFitness :12.4f}, isInternalAllowed: {str(isInternalAllowed) :5s}, isDisplaceAllowed: {str(isDisplaceAllowed) :5s}", end='')

            # Population update:
            pop = self.UpdatePop(pop, elitePop)
        
        # Print the message if GA early stopped:
        if isPrintMessage:
            if isEarlyStopping:
                print('...Early stoping !')
            else:
                print("")
        
        # Output the final result:
        minGene, minGeneInfo = self.GetBestFeasibleGene(pop, isEarlyStopping)
        if minGene is None:
            minGene = pop[0]
            minGeneInfo = self.GetFitness(minGene)
            if isPrintMessage: print('-' * 50 + '\n' + "Warning: Cannot find any feasible result, so only return the gene which has lowest fitness." + '\n' + '-' * 50)
        
        return minGene, minGeneInfo, pop, bestFitnessHistory