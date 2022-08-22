from scipy.sparse import coo_matrix, csr_matrix

import torch
from torch_geometric.data import HeteroData

from .truss import Truss
from .type  import MemberType, SupportType, MetapathType, TaskType
from .utils import GetCenter, GetAngles, TrussNotSolvedError, InvalidTaskTypeError


class TrussHeteroDataCreator:
    def __init__(self, metapathType: MetapathType = MetapathType.NO_IMPLICIT, taskType: TaskType = TaskType.OPTIMIZATION):
        self.metapathType = metapathType
        self.taskType     = taskType
        self.jointIndexToID, self.memberIndexToID, self.source, self.truss = [], [], None, None

    def FromJSON(self, trussJSONFile: str, trussDim: int, forceScale=1., displaceScale=1., positionScale=1., usedMemberTypes: list[MemberType] = None, 
                       fixedMemberType=MemberType(1., 1e7, 0.1), isUseFixed=True, isOutputFile=False):
        truss = Truss(trussDim).LoadFromJSON(trussJSONFile, isOutputFile=isOutputFile)
        if not isOutputFile: 
            truss.Solve()

        fixedInternals, fixedDisplaces = self.__GetFixedInternalAndDisplace(truss, fixedMemberType) if isUseFixed else (None, None)
        self.truss    , self.source    = truss, trussJSONFile
        return self.__CreateGraphData(
            truss, 
            self.__CreateJointData (truss, forceScale, positionScale, displaceScale , fixedDisplaces ), 
            self.__CreateMemberData(truss, forceScale, positionScale, fixedInternals, usedMemberTypes), 
            *self.__CreateEdges(truss)
        )
    
    def FromTruss(self, truss: Truss, forceScale=1., displaceScale=1., positionScale=1., usedMemberTypes: list[MemberType] = None, 
                        fixedMemberType=MemberType(1., 1e7, 0.1), isUseFixed=True, trussSrc=None):
        if not truss.isSolved:
            truss.Solve()

        fixedInternals, fixedDisplaces = self.__GetFixedInternalAndDisplace(truss, fixedMemberType) if isUseFixed else (None, None)
        self.truss    , self.source    = truss, trussSrc
        return self.__CreateGraphData(
            truss, 
            self.__CreateJointData (truss, forceScale, positionScale, displaceScale , fixedDisplaces ), 
            self.__CreateMemberData(truss, forceScale, positionScale, fixedInternals, usedMemberTypes), 
            *self.__CreateEdges(truss)
        )

    def AddDenseEdges(self, graphData: HeteroData):
        if not self.truss:
            raise RuntimeError("No truss has been assigned.")

        nJoint, nMember = self.truss.nJoint, self.truss.nMember

        jointToMemberEdge = [[], []]
        for i in range(nJoint):
            for j in range(nMember):
                jointToMemberEdge[0].append(i)
                jointToMemberEdge[1].append(j)

        memberToJointEdge = [jointToMemberEdge[1], jointToMemberEdge[0]]
        graphData['joint' , 'jFCm', 'member'].edge_index = torch.tensor(jointToMemberEdge, dtype=torch.long)
        graphData['member', 'mFCj', 'joint' ].edge_index = torch.tensor(memberToJointEdge, dtype=torch.long)

        if self.metapathType == MetapathType.USE_IMPLICIT:
            jointToJointEdge = [[], []]
            for i in range(nJoint):
                for j in range(nJoint): 
                    jointToJointEdge[0].append(i)
                    jointToJointEdge[1].append(j)

            memberToMemberEdge = [[], []]
            for i in range(nMember):
                for j in range(nMember): 
                    memberToMemberEdge[0].append(i)
                    memberToMemberEdge[1].append(j)

            graphData['joint' , 'jFCj', 'joint' ].edge_index = torch.tensor(jointToJointEdge  , dtype=torch.long)
            graphData['member', 'mFCm', 'member'].edge_index = torch.tensor(memberToMemberEdge, dtype=torch.long)

        return graphData
    

    def AddMasterNode(self, graphData: HeteroData, embeddingDim=1, fillValue=1.):
        if not self.truss:
            raise RuntimeError("No truss has been assigned.")
        
        nJoint, nMember = self.truss.nJoint, self.truss.nMember

        jointToMasterEdge  = [[i for i in range(nJoint )], [0 for _ in range(nJoint )]]
        masterToJointEdge  = [[0 for _ in range(nJoint )], [i for i in range(nJoint )]]
        memberToMasterEdge = [[i for i in range(nMember)], [0 for _ in range(nMember)]]
        masterToMemberEdge = [[0 for _ in range(nMember)], [i for i in range(nMember)]]

        graphData['master'].x = torch.tensor([[fillValue] for _ in range(embeddingDim)])
        graphData['joint' , 'j2M', 'master'].edge_index = torch.tensor(jointToMasterEdge , dtype=torch.long)
        graphData['master', 'M2j', 'joint' ].edge_index = torch.tensor(masterToJointEdge , dtype=torch.long)
        graphData['member', 'm2M', 'master'].edge_index = torch.tensor(memberToMasterEdge, dtype=torch.long)
        graphData['master', 'M2m', 'member'].edge_index = torch.tensor(masterToMemberEdge, dtype=torch.long)

        return graphData
    
    @staticmethod
    def __GetEdgeFromSparse(csrMat: csr_matrix):
        csrMat[csrMat > 1] = 1
        cooMat = coo_matrix(csrMat)
        row, col = cooMat.row.tolist(), cooMat.col.tolist()
        return [row, col]
    
    @staticmethod
    def __GetFixedInternalAndDisplace(truss: Truss, fixedMemberType: MemberType):
        truss = truss.Copy()
        for memberID in truss.GetMemberIDs():
            truss.SetMemberType(memberID, fixedMemberType)

        truss.Solve()
        return truss.GetInternalStresses(), truss.GetDisplacements()
    
    def __CreateJointData(self, truss, forceScale, positionScale, displaceScale, fixedDisplaces):
        # Clear the mapping which is from joint indexes in dataset to joint IDs in the truss:
        self.jointIndexToID.clear()

        # For [optimization] task:
        if self.taskType == TaskType.OPTIMIZATION:
            joints, forces, dim, jointData = truss.GetJoints(), truss.GetForces(), truss.dim, {'x': [], 'y': []}
            for jointID, (position, supportType) in joints.items():
                # X data:
                if fixedDisplaces is None:
                    jointData['x'].append([
                        *([p / positionScale for p in position]),
                        *([f / forceScale    for f in forces        [jointID]] if jointID in forces        else [0.] * dim),
                        float(supportType != SupportType.NO)
                    ])
                else:
                    jointData['x'].append([
                        *([p / positionScale for p in position]),
                        *([f / forceScale    for f in forces        [jointID]] if jointID in forces         else [0.] * dim),
                        *([d / displaceScale for d in fixedDisplaces[jointID]] if jointID in fixedDisplaces else [0.] * dim),
                        float(supportType != SupportType.NO)
                    ])

                # Record a mapping which is from joint indexes in dataset to joint IDs in the truss:
                self.jointIndexToID.append(jointID)

        # For [regression] task:
        elif self.taskType == TaskType.REGRESSION:
            joints, forces, displaces, dim, jointData = truss.GetJoints(), truss.GetForces(), truss.GetDisplacements(), truss.dim, {'x': [], 'y': []}
            for jointID, (position, supportType) in joints.items():
                # X data:
                if fixedDisplaces is None:
                    jointData['x'].append([
                        *([p / positionScale for p in position]),
                        *([f / forceScale    for f in forces        [jointID]] if jointID in forces         else [0.] * dim),
                        float(supportType != SupportType.NO)
                    ])
                else:
                    jointData['x'].append([
                        *([p / positionScale for p in position]),
                        *([f / forceScale    for f in forces        [jointID]] if jointID in forces         else [0.] * dim),
                        *([d / displaceScale for d in fixedDisplaces[jointID]] if jointID in fixedDisplaces else [0.] * dim),
                        float(supportType != SupportType.NO)
                    ])

                # Y data:
                if not truss.isSolved: raise TrussNotSolvedError("Must do structural analysis first to create regression targets.")
                target = [d / displaceScale for d in displaces[jointID].tolist()] if jointID in displaces else [0.] * truss.dim
                jointData['y'].append(target)

                # Record a mapping which is from joint indexes in dataset to joint IDs in the truss:
                self.jointIndexToID.append(jointID)
        else:
            raise InvalidTaskTypeError(f"Invalid task type [{self.taskType}].")

        return jointData
    
    def __CreateMemberData(self, truss, forceScale, positionScale, fixedInternals, usedMemberTypes):
        # Clear the mapping which is from member indexes in dataset to member IDs in the truss:
        self.memberIndexToID.clear()

        # For [optimization] task:
        if self.taskType == TaskType.OPTIMIZATION:
            joints, members, memberData = truss.GetJoints(), truss.GetMembers(), {'x': [], 'y': []}
            for memberID, (jointID0, jointID1, member) in members.items():
                # X data:
                p0, p1 = joints[jointID0][0], joints[jointID1][0]
                if fixedInternals is None:
                    memberData['x'].append([
                        *[p / positionScale for p in GetCenter(p0, p1)],
                        *GetAngles(p0, p1),
                        member.length / positionScale
                    ])
                else:
                    memberData['x'].append([
                        *[p / positionScale for p in GetCenter(p0, p1)],
                        *GetAngles(p0, p1),
                        member.length / positionScale,
                        (fixedInternals[memberID] / forceScale if memberID in fixedInternals else 0.)
                    ])

                # Y data (for imiation learning):
                if usedMemberTypes is not None:
                    memberData['y'].append([usedMemberTypes.index(member.memberType)])

                # Record a mapping which is from member indexes in dataset to member IDs in the truss:
                self.memberIndexToID.append(memberID)
        
        # For [regression] task:
        elif self.taskType == TaskType.REGRESSION:
            joints, members, stresses, memberData = truss.GetJoints(), truss.GetMembers(), truss.GetInternalStresses(), {'x': [], 'y': []}
            for memberID, (jointID0, jointID1, member) in members.items():
                # X data:
                if fixedInternals is None:
                    p0, p1 = joints[jointID0][0], joints[jointID1][0]
                    memberData['x'].append([
                        *[p / positionScale for p in GetCenter(p0, p1)],
                        *GetAngles(p0, p1),
                        member.length / positionScale,
                        member.memberType.a
                    ])
                else:
                    p0, p1 = joints[jointID0][0], joints[jointID1][0]
                    memberData['x'].append([
                        *[p / positionScale for p in GetCenter(p0, p1)],
                        *GetAngles(p0, p1),
                        member.length / positionScale,
                        (fixedInternals[memberID] / forceScale if memberID in fixedInternals else 0.),
                        member.memberType.a
                    ])

                # Y data:
                if not truss.isSolved: raise TrussNotSolvedError("Must do structural analysis first to create regression targets.")
                memberData['y'].append([stresses[memberID] / forceScale] if memberID in stresses else [0.])

                # Record a mapping which is from member indexes in dataset to member IDs in the truss:
                self.memberIndexToID.append(memberID)
        else:
            raise InvalidTaskTypeError(f"Invalid task type [{self.taskType}].")
        
        return memberData
    
    def __CreateEdges(self, truss):
        if not (self.jointIndexToID and self.memberIndexToID):
            raise ValueError("not (self.jointIndexToID and self.memberIndexToID)")

        jointIndexList, memberIndexList = [], []
        for i, (_, (jointID0, jointID1, _)) in enumerate(truss.GetMembers().items()):
            jointIndexList.extend([self.jointIndexToID.index(jointID0), self.jointIndexToID.index(jointID1)])
            memberIndexList.extend([i, i])
        
        jointToMemberEdge = [jointIndexList, memberIndexList]
        memberToJointEdge = [memberIndexList, jointIndexList]

        jointToMemberAdj  = coo_matrix(([1] * len(jointIndexList) , jointToMemberEdge), shape=(truss.nJoint , truss.nMember))
        memberToJointAdj  = coo_matrix(([1] * len(memberIndexList), memberToJointEdge), shape=(truss.nMember, truss.nJoint ))
        
        if self.metapathType == MetapathType.USE_IMPLICIT:
            jointToJointEdge   = self.__GetEdgeFromSparse(jointToMemberAdj @ memberToJointAdj)
            memberToMemberEdge = self.__GetEdgeFromSparse(memberToJointAdj @ jointToMemberAdj)
            return [jointToMemberEdge, memberToJointEdge, jointToJointEdge, memberToMemberEdge]

        return [jointToMemberEdge, memberToJointEdge, None, None]
    
    def __CreateGraphData(self, truss, jointData, memberData, jointToMemberEdge, memberToJointEdge, jointToJointEdge=None, memberToMemberEdge=None):
        bigraphData = HeteroData()
        bigraphData['src'] = self.source
        bigraphData['originWeight'] = truss.weight

        bigraphData['joint'] .x = torch.tensor(jointData ['x'], dtype=torch.float32)
        bigraphData['member'].x = torch.tensor(memberData['x'], dtype=torch.float32)

        if jointData ['y']: bigraphData['joint'].y = torch.tensor(jointData['y'], dtype=torch.float32)
        if memberData['y']: 
            if truss.isSolved:
                bigraphData['member'].y = torch.tensor(memberData['y'], dtype=torch.float32)
            else:
                bigraphData['member'].y = torch.tensor(memberData['y'], dtype=torch.long)

        bigraphData['joint' , 'j2m', 'member'].edge_index = torch.tensor(jointToMemberEdge, dtype=torch.long)
        bigraphData['member', 'm2j', 'joint' ].edge_index = torch.tensor(memberToJointEdge, dtype=torch.long)

        if self.metapathType == MetapathType.USE_IMPLICIT:
            bigraphData['joint' , 'j2j', 'joint' ].edge_index = torch.tensor(jointToJointEdge  , dtype=torch.long)
            bigraphData['member', 'm2m', 'member'].edge_index = torch.tensor(memberToMemberEdge, dtype=torch.long)
        
        return bigraphData