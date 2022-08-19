import numpy as np
import json
import copy
from pprint import pformat

from .utils import IsZero, IsZeroVector, GetLength, CheckDim, DimensionError, TrussNotStableError, InvaildJointError, TrussNotSolvedError, NotAllBeSetError
from .type  import MemberType, SupportType


class Member:
    def __init__(self, joint0, joint1, dim=3, memberType=MemberType()):
        self.__dim = CheckDim(dim)
        if len(joint0) != dim or len(joint1) != dim:
            raise DimensionError(f"Dimension of each joint must be {dim}, but got dim(joint0) = {len(joint0)} and dim(joint1) = {len(joint1)}.")
        
        self.__joint0     = joint0
        self.__joint1     = joint1
        self.__memberType = memberType
        self.__length     = sum((joint1[i] - joint0[i]) ** 2. for i in range(dim)) ** 0.5
    
    def __repr__(self):
        return f"Member[{self.__joint0}, {self.__joint1}, k={self.e * self.a / self.__length :.4f}]"
    
    @property
    def dim(self):
        return self.__dim
    
    @property
    def e(self):
        return self.__memberType.e
    
    @property
    def a(self):
        return self.__memberType.a
    
    @property
    def density(self):
        return self.__memberType.density

    @property
    def memberType(self):
        return self.__memberType.Copy()
    
    @memberType.setter
    def memberType(self, other):
        self.__memberType.Set(other)
    
    @property
    def length(self):
        return self.__length
    
    @property
    def weight(self):
        return self.a * self.__length * self.density
    
    @property
    def k(self):
        return self.e * self.a / self.__length
    
    @property
    def cosines(self):
        joint0, joint1, length = self.__joint0, self.__joint1, self.__length
        return [(joint1[i] - joint0[i]) / length for i in range(self.dim)]
    
    @property
    def matK(self):
        if self.dim == 3:
            l, m, n = self.cosines
            l2, m2, n2, lm, ln, mn = l ** 2., m ** 2., n ** 2., l * m, l * n, m * n
            return self.k * np.array([
                [ l2,  lm,  ln, -l2, -lm, -ln],
                [ lm,  m2,  mn, -lm, -m2, -mn],
                [ ln,  mn,  n2, -ln, -mn, -n2],
                [-l2, -lm, -ln,  l2,  lm,  ln],
                [-lm, -m2, -mn,  lm,  m2,  mn],
                [-ln, -mn, -n2,  ln,  mn,  n2],
            ])
        else:
            c, s = self.cosines
            c2, s2, cs = c ** 2., s ** 2., c * s
            return self.k * np.array([
                [ c2,  cs, -c2, -cs],
                [ cs,  s2, -cs, -s2],
                [-c2, -cs,  c2,  cs],
                [-cs, -s2,  cs,  s2]
            ])
    
    # Judge whether the input force vector is tension for this member or not:
    def IsTension(self, forceVec):
        memberVec = np.array(self.__joint1) - np.array(self.__joint0)
        return np.dot(memberVec, forceVec) > 0 
    
    # Change the position of joint:
    def SetPosition(self, jointID_0or1, position):
        if   jointID_0or1 == 0: self.__joint0 = position
        elif jointID_0or1 == 1: self.__joint1 = position
        else: raise KeyError("[jointID_0or1] must be 0 or 1.")
        self.__length = sum((self.__joint1[i] - self.__joint0[i]) ** 2. for i in range(self.__dim)) ** 0.5

    # Serialize this member:
    def Serialize(self):
        return {"joint0": list(self.__joint0), "joint1": list(self.__joint1), "memberType": self.__memberType.Serialize()}
    
    # Copy this member:
    def Copy(self):
        return Member(tuple([v for v in self.__joint0]), tuple([v for v in self.__joint1]), self.__dim, self.memberType.Copy())


class Truss:
    def __init__(self, dim):
        # User conditions:
        self.__dim     = CheckDim(dim)  # (int ) Dimension of this truss
        self.__joints  = {}             # (dict) {jointID : ((px, py, pz), supportType) }
        self.__forces  = {}             # (dict) {jointID : (fx, fy, fz)                }
        self.__members = {}             # (dict) {memberID: (jointID0, jointID1, member)}
        
        # Solved results:
        self.__displace = None          # (dict) {jointID : np.array([dx, dy, dz])}
        self.__external = None          # (dict) {jointID : np.array([fx, fy, fz])}
        self.__internal = None          # (dict) {memberID: internalForce         } (Not internal stress !)
        self.__isSolved = False         # (bool) Indicate whether this truss has been solved.

    def __repr__(self):
        return (
            super().__repr__() + "\n" +
            "-" * 30 + "\nJoints :\n"    + "-" * 30 + f"\n{pformat(self.__joints)}\n\n"  + 
            "-" * 30 + "\nForces :\n"    + "-" * 30 + f"\n{pformat(self.__forces)}\n\n"  + 
            "-" * 30 + "\nMembers :\n"   + "-" * 30 + f"\n{pformat(self.__members)}\n\n" +
            "-" * 30 +  "\nDisplaces:\n" + "-" * 30 + f"\n{pformat(self.__displace) if self.__isSolved else '(Not Solved)'}\n\n" +
            "-" * 30 +  "\nInternals:\n" + "-" * 30 + f"\n{pformat(self.__internal) if self.__isSolved else '(Not Solved)'}\n\n" +
            "-" * 30 +  "\nExternals:\n" + "-" * 30 + f"\n{pformat(self.__external) if self.__isSolved else '(Not Solved)'}\n\n"
        )
    
    @property
    def dim(self):
        return self.__dim
    
    @property
    def nJoint(self):
        return len(self.__joints)
    
    @property
    def nMember(self):
        return len(self.__members)
    
    @property
    def nForce(self):
        return len(self.__forces)
    
    @property
    def nSupport(self):
        return len(list(filter(lambda x: x[-1] != SupportType.NO, self.__joints.values())))
    
    @property
    def nResistance(self):
        return sum(SupportType.GetResistanceNumber(supportType, self.__dim) for _, supportType in self.__joints.values())
    
    @property
    def isStable(self):
        if self.__dim == 2:
            return self.nMember + self.nResistance >= self.nJoint * self.__dim
        
        nResistance = self.nResistance
        return (nResistance >= 6) and (self.nMember + nResistance >= self.nJoint * self.__dim)
    
    @property
    def weight(self):
        return sum(member.weight for _, _, member in self.__members.values())
    
    @property
    def isSolved(self):
        return self.__isSolved
    
    def AddNewJoint(self, vector, supportType=SupportType.NO):
        self.__joints[len(self.__joints)] = (tuple(float(vector[i]) for i in range(self.__dim)), supportType)
    
    def AddExternalForce(self, jointID, vector):
        if jointID not in self.__joints:
            raise InvaildJointError(f"No such joint [{jointID}], can't add force on it.")

        if not IsZeroVector(vector):
            self.__forces[jointID] = tuple(float(vector[i]) for i in range(self.__dim))
        
    def AddNewMember(self, jointID0, jointID1, memberType):
        self.__members[len(self.__members)] = (jointID0, jointID1, Member(self.__joints[jointID0][0], 
                                                                          self.__joints[jointID1][0],
                                                                          self.__dim, memberType))
    def SetJointPosition(self, jointID, position):
        self.__joints[jointID] = (position, self.__joints[jointID][-1])
        for jointID0, jointID1, member in self.__members.values():
            if jointID0 == jointID: member.SetPosition(0, position)
            if jointID1 == jointID: member.SetPosition(1, position)
    
    def SetJointPositions(self, jointPositionDict):
        for jointID, position in jointPositionDict.items():
            self.SetJointPosition(jointID, position)
    
    def SetSupportType(self, jointID, supportType):
        self.__joints[jointID][1] = supportType

    def SetSupportTypes(self, supportTypeDict):
        for jointID, supportType in supportTypeDict.items():
            self.__joints[jointID][1] = supportType
    
    def SetMemberType(self, memberID, memberType):
        self.__members[memberID][2].memberType = memberType
    
    def SetMemberTypes(self, memberTypeDict, isCheckAllSet=False):
        if isCheckAllSet and self.__members.keys() - memberTypeDict.keys():
            raise NotAllBeSetError("Didn't set member types to all members.")

        for memberID, memberType in memberTypeDict.items():
            self.__members[memberID][2].memberType = memberType
    
    def SetMemberConnect(self, memberID, connect):
        member = self.__members[memberID][-1]
        member.SetPosition(0, self.__joints[connect[0]][0])
        member.SetPosition(1, self.__joints[connect[1]][0])
        self.__members[memberID] = connect + (member,)

    def SetMemberConnects(self, memberConnectDict):
        for memberID, connect in memberConnectDict.items():
            self.SetMemberConnect(memberID, connect)
    
    def GetJointPosition(self, jointID):
        return self.__joints[jointID][0]
    
    def GetJointPositions(self):
        return {jointID: position for jointID, (position, _) in self.__joints.items()}
    
    def GetSupportType(self, jointID):
        return self.__joints[jointID][1]
    
    def GetSupportTypes(self):
        return {jointID: supportType for jointID, (_, supportType) in self.__joints.items()}
    
    def GetMemberType(self, memberID):
        return self.__members[memberID][2].memberType
    
    def GetMemberTypes(self):
        return {memberID: member.memberType for memberID, (_, _, member) in self.__members.items()}
    
    def GetMemberConnect(self, memberID):
        member = self.__members[memberID]
        return member[0], member[1]
    
    def GetMemberFromConnect(self, connect):
        for jointID0, jointID1, member in self.__members.values():
            if (jointID0 == connect[0]) and (jointID1 == connect[1]):
                return member
    
    def GetForce(self, jointID):
        return self.__forces[jointID]
    
    def GetJoints(self, isProtect=True):
        return copy.deepcopy(self.__joints) if isProtect else self.__joints
    
    def GetMembers(self, isProtect=True):
        return copy.deepcopy(self.__members) if isProtect else self.__members
    
    def GetForces(self, isProtect=True):
        return copy.deepcopy(self.__forces) if isProtect else self.__forces
    
    def GetDisplacements(self, isProtect=True):
        return copy.deepcopy(self.__displace) if isProtect else self.__displace
    
    def GetExternalForces(self, isProtect=True):
        return copy.deepcopy(self.__external) if isProtect else self.__external
    
    def GetInternalForces(self, isProtect=True):
        return copy.deepcopy(self.__internal) if isProtect else self.__internal
    
    def GetInternalStresses(self):
        if self.__internal is not None:
            return {memberID: internal / self.__members[memberID][2].a for memberID, internal in self.__internal.items()}
        
        return None
    
    def GetResistances(self):
        if not self.__isSolved:
            return None
        
        res = {}
        for jointID in self.__joints:
            if self.__joints[jointID][1] != SupportType.NO:  
                if jointID in self.__forces:
                    res[jointID] = self.__external.get(jointID, np.zeros([self.__dim])) - self.__forces[jointID]
                else:
                    res[jointID] = self.__external.get(jointID, np.zeros([self.__dim]))

        return res
    
    def GetJointIDs(self):
        return [jointID for jointID in self.__joints]
    
    def GetMemberIDs(self):
        return [memberID for memberID in self.__members]
    
    def GetUsedMemberTypes(self):
        return set([member.memberType for _, _, member in self.__members.values()])
    
    # Get the full dimension vector of external forces padding by 0:
    def GetExternalForceVector(self):
        return np.array([self.__forces.get(i, np.zeros([self.__dim])) for i in range(self.nJoint)]).ravel()
        
    # Get the structural matrix K:
    def GetKMatrix(self):
        dim  = self.__dim
        matK = np.zeros([self.nJoint * dim, self.nJoint * dim])
        for jointID0, jointID1, member in self.__members.values():
            memberK = member.matK
            for i, x in [(0, jointID0 * dim), (dim, jointID1 * dim)]:
                for j, y in [(0, jointID0 * dim), (dim, jointID1 * dim)]:
                    matK[x: x + dim, y: y + dim] += memberK[i: i + dim, j: j + dim]
            
        return matK
    
    # Get a mask which indicate the indexes of unknown displacement dimensions:
    def GetDisplacementUnknownMask(self):
        dim = self.__dim
        displaceUnknownMask = np.bool8(np.ones([self.nJoint * dim]))
        for jointID, (_, supportType) in self.__joints.items():
            mask = SupportType.GetResistanceMask(supportType, dim)
            displaceUnknownMask[jointID * dim: (jointID + 1) * dim] = np.logical_not(mask)
        
        return displaceUnknownMask
        
    # Solve the linear system => K * u = f:
    def Solve(self):

        # Check whether this truss is stable or not:
        if not self.isStable:
            raise TrussNotStableError("The truss is not stable !")
        
        # Get linear system:
        dim  = self.__dim
        matK = self.GetKMatrix()
        vecF = self.GetExternalForceVector()
        mask = self.GetDisplacementUnknownMask()

        # Solve displacements:
        vecD = np.zeros([self.nJoint * dim])
        vecD[mask] = np.linalg.solve(matK[mask, :][:, mask], vecF[mask])
        self.__displace = {jointID: d for jointID in self.__joints 
                           if not IsZeroVector(d := vecD[jointID * dim: (jointID + 1) * dim])}
        
        # Solve resistances:
        mask = np.logical_not(mask)
        vecF[mask] = (matK[mask, :] @ (vecD.reshape(-1, 1))).ravel()
        self.__external = {jointID: f for jointID in self.__joints
                           if not IsZeroVector(f := vecF[jointID * dim: (jointID + 1) * dim])}
        
        # Solve all the internal forces:
        internal = {}
        for memberID, (jointID0, jointID1, member) in self.__members.items():
            index = list(range(jointID0 * dim, (jointID0 + 1) * dim)) + list(range(jointID1 * dim, (jointID1 + 1) * dim))
            vecI  = (member.matK[dim:] @ vecD[index].reshape(-1, 1)).ravel()
            if not IsZero(valI := (1. if member.IsTension(vecI) else -1.) * GetLength(vecI)):
                internal[memberID] = valI
        
        self.__internal = internal
        
        # Return results:
        self.__isSolved = True
    
    # Serialize this truss:
    def Serialize(self):
        data = {
            'joint'   : [None for _ in self.__joints  ], 
            'force'   : [None for _ in self.__forces  ],
            'member'  : [None for _ in self.__members ]
        }

        for jointID, (vector, supportType) in self.__joints.items():
            data["joint"][jointID ] = [list(vector), SupportType.GetFromType(supportType)]
        
        for memberID, (jointID0, jointI1, member) in self.__members.items():
            data["member"][memberID] = [[jointID0, jointI1], member.memberType.Serialize()]
        
        for i, (jointID, vector) in enumerate(self.__forces.items()):
            data["force"][i] = [jointID, list(vector)]

        if self.__isSolved:
            data['displace'] = [None for _ in self.__displace]
            data['external'] = [None for _ in self.__external]
            data['internal'] = [None for _ in self.__internal]
            data['weight'  ] = self.weight

            for i, (jointID, vector) in enumerate(self.__displace.items()):
                data["displace"][i] = [jointID, list(vector)]
            
            for i, (jointID, vector) in enumerate(self.__external.items()):
                data["external"][i] = [jointID, list(vector)]

            for i, (memberID, force) in enumerate(self.__internal.items()):
                data["internal"][i] = [memberID, float(force)]
        
        return data
    
    # Load truss data from a .json file:
    def LoadFromJSON(self, path=None, isOutputFile=False, data=None):
        if data is None:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        for vector, supportType in data['joint']:
            self.AddNewJoint(vector, SupportType.GetFromString(supportType))
        
        for jointID, vector in data['force']:
            self.AddExternalForce(jointID, vector)
        
        for [jointID0, jointID1], memberType in data['member']:
            self.AddNewMember(jointID0, jointID1, MemberType(*memberType))

        if isOutputFile:
            self.__isSolved = True
            self.__displace = {jointID : np.array(vector) for jointID , vector in data['displace']}
            self.__external = {jointID : np.array(vector) for jointID , vector in data['external']}
            self.__internal = {memberID: float(force)     for memberID, force  in data['internal']}
        
        return self
 
    # Dump all the structural analysis results into a .json file:
    def DumpIntoJSON(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.Serialize(), f, ensure_ascii=False)
    
    # Check whether all internal forces are in allowable range or not:
    def IsInternalStressAllowed(self, limit, isGetSumViolation=False, isGetSumNonViolation=False):
        if self.__isSolved:
            if isGetSumViolation:
                violation = sum(f - limit for memberID, force in self.__internal.items() if (f := abs(force) / self.__members[memberID][2].a) > limit)
                isVio     = IsZero(violation)
            else:
                violation = {memberID: f - limit for memberID, force in self.__internal.items() if (f := abs(force) / self.__members[memberID][2].a) > limit}
                isVio     = len(violation) == 0
            
            if isGetSumNonViolation:
                nonViolation = sum(limit - f for memberID, force in self.__internal.items() if (f := abs(force) / self.__members[memberID][2].a) <= limit)
                return isVio, violation, nonViolation
            
            return isVio, violation
        
        raise TrussNotSolvedError("Haven't done structural analysis yet.")
    
    # Check whether all internal displacements are in allowable range or not:
    def IsDisplacementAllowed(self, limit, isGetSumViolation=False, isGetSumNonViolation=False):
        if self.__isSolved:
            if isGetSumViolation:
                violation = sum(l - limit for displace in self.__displace.values() if (l := GetLength(displace)) > limit)
                isVio     = IsZero(violation)
            else:
                violation = {jointID: l - limit for jointID, displace in self.__displace.items() if (l := GetLength(displace)) > limit}
                isVio     = len(violation) == 0
            
            if isGetSumNonViolation:
                nonViolation = sum(limit - l for displace in self.__displace.values() if (l := GetLength(displace)) <= limit)
                return isVio, violation, nonViolation
            
            return isVio, violation
        
        raise TrussNotSolvedError("Haven't done structural analysis yet.")
    
    # Copy this truss:
    def Copy(self):
        return Truss(self.__dim).LoadFromJSON(data=self.Serialize(), isOutputFile=self.__isSolved)