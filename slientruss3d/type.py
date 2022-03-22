import numpy as np

from .utils import CheckDim, IsZero, InvalidSupportTypeError

class MemberType:
    def __init__(self, a=1., e=1., density=1.):
        self.a       = float(a)
        self.e       = float(e)
        self.density = float(density)
    
    def __repr__(self):
        return f"MemberType(a={self.a}, e={self.e}, density={self.density})"
    
    def __eq__(self, other):
        return IsZero(self.a - other.a) and IsZero(self.e - other.e) and IsZero(self.density - other.density)
    
    def __hash__(self):
        return (self.a, self.e, self.density).__hash__()
    
    def Set(self, other):
        self.a, self.e, self.density = other.a, other.e, other.density
    
    def Serialize(self):
        return [self.a, self.e, self.density]
    
    def Copy(self):
        return MemberType(self.a, self.e, self.density)


class SupportType:
    NO       = 0
    PIN      = 1
    ROLLER_X = 2
    ROLLER_Y = 3
    ROLLER_Z = 4

    @staticmethod
    def GetResistanceNumber(supportType, dim):
        if supportType == SupportType.PIN:
            return dim
        elif supportType in (SupportType.ROLLER_X, SupportType.ROLLER_Y, SupportType.ROLLER_Z):
            return 1
        elif supportType == SupportType.NO:
            return 0
        else: 
            raise InvalidSupportTypeError(f"[GetResistanceNumber] No such support type [{supportType}] !")
    
    @staticmethod
    def GetResistanceMask(supportType, dim):
        if CheckDim(dim) == 3:
            if supportType == SupportType.PIN:
                return np.array([True, True, True])
            elif supportType == SupportType.ROLLER_X:
                return np.array([True, False, False])
            elif supportType == SupportType.ROLLER_Y:
                return np.array([False, True, False])
            elif supportType == SupportType.ROLLER_Z:
                return np.array([False, False, True])
            elif supportType == SupportType.NO:
                return np.array([False, False, False])
            else:
                InvalidSupportTypeError(f"[GetResistanceMask] No such {dim}D-support type [{supportType}] !")

        else:
            if supportType == SupportType.PIN:
                return np.array([True, True])
            elif supportType == SupportType.ROLLER_X:
                return np.array([True, False])
            elif supportType == SupportType.ROLLER_Y:
                return np.array([False, True])
            elif supportType == SupportType.NO:
                return np.array([False, False])
            else:
                raise InvalidSupportTypeError(f"[GetResistanceMask] No such {dim}D-support type [{supportType}] !")

    @staticmethod
    def GetFromString(string):
        try:
            return eval(f"SupportType.{string}")
        except:
            raise InvalidSupportTypeError(f"[GetFromString] No such support type [{string}] !")
    
    @staticmethod
    def GetFromType(supportType):
        types = filter(lambda x: not callable(x), dir(SupportType))
        for t in types:
            if getattr(SupportType, t) == supportType:
                return t


class MetapathType:
    USE_IMPLICIT = 0
    NO_IMPLICIT  = 1


class TaskType:
    OPTIMIZATION = 0
    REGRESSION   = 1


class LinkType:
    LeftBottom_RightTop = 0
    RightBottom_LeftTop = 1
    Cross               = 2
    Random              = 3


class GenerateMethod:
    DFS    = 0
    BFS    = 1
    Random = 2