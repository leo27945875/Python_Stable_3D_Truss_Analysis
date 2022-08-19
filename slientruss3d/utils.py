from turtle import position
import numpy as np
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d


# ----------------------------- Constant -----------------------------
INF = float("inf")


# ----------------------------- Plot -----------------------------
class Arrow3D(FancyArrowPatch):
    def __init__(self, posA, posB, *args, **kwargs):
        super().__init__((0,0), (0,0), *args, **kwargs)
        self._verts3d =  list(zip(posA, posB))

    def do_3d_projection(self, renderer=None):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
        self.set_positions((xs[0],ys[0]),(xs[1],ys[1]))
        return np.min(zs)


class Arrow2D(FancyArrowPatch):
    pass


def SetAxesEqual(ax, dim):
    if dim == 3:
        xLimits = ax.get_xlim3d()
        yLimits = ax.get_ylim3d()
        zLimits = ax.get_zlim3d()

        xRange = abs(xLimits[1] - xLimits[0])
        yRange = abs(yLimits[1] - yLimits[0])
        zRange = abs(zLimits[1] - zLimits[0])

        xMiddle = np.mean(xLimits)
        yMiddle = np.mean(yLimits)
        zMiddle = np.mean(zLimits)

        plotRadius = 0.5*max([xRange, yRange, zRange])

        ax.set_xlim3d([xMiddle - plotRadius, xMiddle + plotRadius])
        ax.set_ylim3d([yMiddle - plotRadius, yMiddle + plotRadius])
        ax.set_zlim3d([zMiddle - plotRadius, zMiddle + plotRadius])
    else:
        ax.set_aspect('equal')


# ----------------------------- Exception -----------------------------
class InvalidSupportTypeError       (Exception): pass
class InvalidMetapathTypeError      (Exception): pass
class InvalidTaskTypeError          (Exception): pass
class InvalidLinkTypeError          (Exception): pass
class InvalidGenerateMethodError    (Exception): pass
class TrussNotStableError           (Exception): pass
class TrussNotSolvedError           (Exception): pass
class DimensionError                (Exception): pass
class InvaildJointError             (Exception): pass
class EliteNumberTooMuchError       (Exception): pass
class ProbabilityGreaterThanOneError(Exception): pass
class OnlyOneMemberTypeError        (Exception): pass
class MinStressTooLargeError        (Exception): pass
class MinDisplaceTooLargeError      (Exception): pass
class NotAllBeSetError              (Exception): pass
class PinNotEnoughError             (Exception): pass


# ----------------------------- Truss -----------------------------
def CheckDim(dim):
    if dim not in {2, 3}:
        raise DimensionError(f"Dimension of truss and member must be 2 or 3, but got [{dim}].")
    
    return dim


# ----------------------------- Math -----------------------------
def IsZero(num, eps=1e-10):
    return abs(num) < eps


def IsZeroVector(vec, eps=1e-10):
    return IsZero(np.array(vec), eps).all()


def GetLength(vec):
    return (vec ** 2).sum() ** 0.5


def MinNorm(vec, minNorm=1.):
    return vec * max(1., minNorm / np.linalg.norm(vec))


def GetPowerset(s):
    x = len(s)
    for i in range(1 << x):
        yield  [s[j] for j in range(x) if (i & (1 << j))]


def GetCenter(position0, position1):
    return [0.5 * (v0 + v1) for v0, v1 in zip(position0, position1)]


def GetAngles(position0, position1):
    p0, p1 = (position0, position1) if position0[-1] < position1[-1] else (position1, position0)
    vec = [(v1 - v0) for v0, v1 in zip(p0, p1)]
    vLength, xyLength = sum(v ** 2. for v in vec) ** 0.5, sum(v ** 2. for v in vec[:2]) ** 0.5
    
    if IsZero(xyLength):
        return xyLength / vLength, vec[2] / vLength, 0., 0.

    return xyLength / vLength, vec[2] / vLength, vec[1] / xyLength, vec[0] / xyLength


# ----------------------------- Flow Control -----------------------------
def InfinteLoop():
    i = 0
    while True:
        yield i
        i += 1