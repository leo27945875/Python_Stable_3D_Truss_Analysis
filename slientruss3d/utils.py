import time
import numpy as np
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d


# ----------------------------- Plot -----------------------------
class Arrow3D(FancyArrowPatch):
    def __init__(self, posA, posB, *args, **kwargs):
        FancyArrowPatch.__init__(self, (0,0), (0,0), *args, **kwargs)
        self._verts3d = list(zip(posA, posB))

    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs  , ys  , _    = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        FancyArrowPatch.draw(self, renderer)


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
class InvalidSupportTypeError(Exception): pass
class TrussNotStableError    (Exception): pass
class DimensionError         (Exception): pass
class InvaildJointError      (Exception): pass
class AddForceOnSupportError (Exception): pass


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
