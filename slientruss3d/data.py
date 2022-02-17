from scipy.sparse import coo_matrix, csr_matrix

import torch
from torch_geometric.data import HeteroData

from .truss import Truss
from .type  import MemberType, SupportType, MetapathType
from .utils import GetCenter, GetAngles


class TrussBipartiteDataCreator:
    def __init__(self, metapathType: MetapathType):
        self.metapathType = metapathType
        self.jointIndexToID, self.memberIndexToID, self.source, self.truss = [], [], None, None
    
    @staticmethod
    def GetFixedInternalAndDisplace(truss: Truss, fixedMemberType: MemberType):
        truss = truss.Copy()
        for memberID in truss.GetMemberIDs():
            truss.SetMemberType(memberID, fixedMemberType)

        truss.Solve()
        return truss.GetInternalStresses(), truss.GetDisplacements()
    
    @staticmethod
    def GetEdgeFromSparse(csrMat: csr_matrix):
        csrMat[csrMat > 1] = 1
        cooMat = coo_matrix(csrMat)
        row, col = cooMat.row.tolist(), cooMat.col.tolist()
        return [row, col]

    def FromJSON(self, trussJSONFile, trussDim, forceScale, displaceScale, positionScale, usedMemberTypes, fixedMemberType=MemberType(1., 1e7, 0.1)):
        truss = Truss(trussDim).LoadFromJSON(trussJSONFile, isOutputFile=False)
        fixedInternals, fixedDisplaces = self.GetFixedInternalAndDisplace(truss, fixedMemberType)
        self.truss    , self.source    = truss, trussJSONFile
        return self.CreateGraphData(truss, 
                                    self.CreateJointData (truss, forceScale, positionScale, displaceScale , fixedDisplaces ), 
                                    self.CreateMemberData(truss, forceScale, positionScale, fixedInternals, usedMemberTypes), 
                                    *self.CreateEdges(truss))
    
    def FromTruss(self, trussID, truss, forceScale, displaceScale, positionScale, usedMemberTypes, fixedMemberType=MemberType(1., 1e7, 0.1)):
        fixedInternals, fixedDisplaces = self.GetFixedInternalAndDisplace(truss, fixedMemberType)
        self.truss    , self.source    = truss, trussID
        return self.CreateGraphData(truss, 
                                    self.CreateJointData (truss, forceScale, positionScale, displaceScale , fixedDisplaces ), 
                                    self.CreateMemberData(truss, forceScale, positionScale, fixedInternals, usedMemberTypes), 
                                    *self.CreateEdges(truss))

    def CreateJointData(self, truss, forceScale, positionScale, displaceScale, fixedDisplaces):
        self.jointIndexToID.clear()
        joints, forces, dim, jointData = truss.GetJoints(), truss.GetForces(), truss.dim, {'x': [], 'y': []}
        for jointID, (position, supportType) in joints.items():
            jointData['x'].append([
                *([p / positionScale for p in position]),
                *([f / forceScale    for f in forces        [jointID]] if jointID in forces         else [0.] * dim),
                *([d / displaceScale for d in fixedDisplaces[jointID]] if jointID in fixedDisplaces else [0.] * dim),
                float(supportType != SupportType.NO)
            ])
            self.jointIndexToID.append(jointID)

        return jointData
    
    def CreateMemberData(self, truss, forceScale, positionScale, fixedInternals, usedMemberTypes):
        self.memberIndexToID.clear()
        joints, members, memberData = truss.GetJoints(), truss.GetMembers(), {'x': [], 'y': []}
        for memberID, (jointID0, jointID1, member) in members.items():
            p0, p1 = joints[jointID0][0], joints[jointID1][0]
            memberData['x'].append([
                *[p / positionScale for p in GetCenter(p0, p1)],
                *GetAngles(p0, p1),
                member.length / positionScale,
                (fixedInternals[memberID] / forceScale if memberID in fixedInternals else 0.)
            ])
            memberData['y'].append([usedMemberTypes.index(member.memberType)])
            self.memberIndexToID.append(memberID)
        
        return memberData
    
    def CreateEdges(self, truss):
        if not (self.jointIndexToID and self.memberIndexToID):
            raise ValueError("not (self.jointIndexToID and self.memberIndexToID)")

        jointIndexList, memberIndexList = [], []
        for i, (_, (jointID0, jointID1, _)) in enumerate(truss.GetMembers().items()):
            jointIndexList.extend([self.jointIndexToID.index(jointID0), self.jointIndexToID.index(jointID1)])
            memberIndexList.extend([i, i])
        
        jointToMemberEdge = [jointIndexList, memberIndexList]
        memberToJointEdge = [memberIndexList, jointIndexList]

        jointToMemberAdj  = coo_matrix(([1] * len(jointIndexList) , jointToMemberEdge), shape=(truss.nJoint, truss.nMember))
        memberToJointAdj  = coo_matrix(([1] * len(memberIndexList), memberToJointEdge), shape=(truss.nMember, truss.nJoint))
        
        if self.metapathType == MetapathType.USE_IMPLICIT:
            jointToJointEdge   = self.GetEdgeFromSparse(jointToMemberAdj @ memberToJointAdj)
            memberToMemberEdge = self.GetEdgeFromSparse(memberToJointAdj @ jointToMemberAdj)
            return [jointToMemberEdge, memberToJointEdge, jointToJointEdge, memberToMemberEdge]

        return [jointToMemberEdge, memberToJointEdge, None, None]
    
    def AddDenseEdges(self, graphData):
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
    

    def AddMasterNode(self, graphData):
        if not self.truss:
            raise RuntimeError("No truss has been assigned.")
        
        nJoint, nMember = self.truss.nJoint, self.truss.nMember

        jointToMasterEdge  = [[i for i in range(nJoint )], [0 for _ in range(nJoint )]]
        masterToJointEdge  = [[0 for _ in range(nJoint )], [i for i in range(nJoint )]]
        memberToMasterEdge = [[i for i in range(nMember)], [0 for _ in range(nMember)]]
        masterToMemberEdge = [[0 for _ in range(nMember)], [i for i in range(nMember)]]

        graphData['master'].x = torch.tensor([[0.]])
        graphData['joint' , 'j2M', 'master'].edge_index = torch.tensor(jointToMasterEdge , dtype=torch.long)
        graphData['master', 'M2j', 'joint' ].edge_index = torch.tensor(masterToJointEdge , dtype=torch.long)
        graphData['member', 'm2M', 'master'].edge_index = torch.tensor(memberToMasterEdge, dtype=torch.long)
        graphData['master', 'M2m', 'member'].edge_index = torch.tensor(masterToMemberEdge, dtype=torch.long)

        return graphData

    
    def CreateGraphData(self, truss, jointData, memberData, jointToMemberEdge, memberToJointEdge, jointToJointEdge=None, memberToMemberEdge=None):
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