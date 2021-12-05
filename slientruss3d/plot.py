import numpy as np
import matplotlib.pyplot as plt

from .utils import Arrow2D, Arrow3D, MinNorm, SetAxesEqual
from .type import SupportType


class TrussPlotter:
    def __init__(self, truss, isDisplaceScale=True, isForceScale=True, isEqualAxis=False, 
                 maxScaledDisplace=5, maxScaledForce=5, pointScale=1.0, arrowScale=1.0, figsize=(10, 10)):
        self.truss           = truss
        self.isDisplaceScale = isDisplaceScale
        self.isForceScale    = isForceScale
        self.isEqualAxis     = isEqualAxis
        self.maxDisplace     = maxScaledDisplace
        self.maxForce        = maxScaledForce
        self.pointScale      = pointScale
        self.arrowScale      = arrowScale
        self.figsize         = figsize
    
    def Plot(self, isSave=True, savePath='./truss.png'):
        dim = self.truss.dim

        plt.figure(figsize=self.figsize)
        if dim == 3:
            ax = plt.axes(projection='3d')
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_zlabel('z')
        else:
            ax = plt.axes()
            ax.set_xlabel('x')
            ax.set_ylabel('y')
        
        joints    = self.truss.GetJoints()
        members   = self.truss.GetMembers()
        internals = self.truss.GetInternalForces()
        externals = self.truss.GetExternalForces()
        displaces = self.truss.GetDisplacements()
        forcedIDs = self.truss.GetForces().keys()

        externalScale   = self.maxForce    / (max(abs(vec).max() for vec in externals.values())) if self.isForceScale    else 1.
        displaceScale   = self.maxDisplace / (max(abs(vec).max() for vec in displaces.values())) if self.isDisplaceScale else 1.
        displacedJoints = {jointID: np.array([*vector]) + np.array(displaces[jointID]) * displaceScale for jointID, (vector, _) in joints.items()}
        
        # To check the max and min axis range in 2D figure:
        if dim == 2:
            maxArrowPos, maxJointPos = np.zeros([dim]), np.zeros([dim])
            minArrowPos, minJointPos = np.zeros([dim]), np.zeros([dim])

        # Plot external forces:
        for jointID, position in displacedJoints.items():
            ax.plot(*position, **self.GetSupportMarker(joints[jointID][-1]), alpha=0.3)
            if jointID in externals:
                arrowEnd = position + MinNorm(externals[jointID] * externalScale, self.maxForce * 0.3)
                if jointID in forcedIDs:
                    ax.add_artist((Arrow3D if dim == 3 else Arrow2D)(position, arrowEnd, color='blueviolet', arrowstyle="->", mutation_scale=20 * self.arrowScale, lw=3 * self.arrowScale))
                else:
                    ax.add_artist((Arrow3D if dim == 3 else Arrow2D)(position, arrowEnd, color='green'     , arrowstyle="->", mutation_scale=20 * self.arrowScale, lw=3 * self.arrowScale))

                # Check the max and min position value of 2D force arrows: 
                if dim == 2:
                    maxArrowPos, minArrowPos = np.array([maxArrowPos, arrowEnd]).max(axis=0), np.array([minArrowPos, arrowEnd]).min(axis=0)

        # Plot internal forces and members:
        maxF, minF = max(internals.values()), min(internals.values())
        for memberID, (jointID0, jointID1, _) in members.items():
            ax.plot(*zip(joints[jointID0][0], joints[jointID1][0]), 'k-')
            if self.truss.isSolved:
                ax.plot(*zip(displacedJoints[jointID0], displacedJoints[jointID1]), 
                        color=self.GetMemberColor(internals[memberID], maxF, minF),
                        linestyle='--')
        
        # Plot joints and displacements:
        for jointID, (vector, supportType) in joints.items():
            ax.plot(*vector, **self.GetSupportMarker(supportType))
            ax.text(*vector, str(jointID), color='white', va="center", ha="center", size=7 * self.pointScale)

            # Check the max and min position value of 2D joints:
            if dim == 2:
                maxJointPos, minJointPos = np.array([maxJointPos, vector]).max(axis=0), np.array([minJointPos, vector]).min(axis=0)
        
        # Set axis range:
        if dim == 2:
            maxPos = np.array([maxArrowPos, maxJointPos]).max(axis=0) * 1.05
            minPos = np.array([minArrowPos, minJointPos]).min(axis=0) * 1.05
            axisRange = []
            for x, y in zip(minPos, maxPos): axisRange.extend([x, y])
            plt.axis(axisRange)
        
        if self.isEqualAxis:
            SetAxesEqual(ax, dim)
        
        if self.isDisplaceScale:
            plt.title("Displacement has been scaled, not real displacement !")

        if isSave:
            plt.savefig(savePath)
        else:
            plt.show()
    
    def GetSupportMarker(self, supportType):
        if supportType == SupportType.PIN:
            return {'color': 'deepskyblue', 'marker': '^', 'markersize': 12 * self.pointScale}
        elif supportType in {SupportType.ROLLER_X, SupportType.ROLLER_Y, SupportType.ROLLER_Z}:
            return {'color': 'deepskyblue', 'marker': 'o', 'markersize': 12 * self.pointScale}
        elif supportType == SupportType.NO:
            return {'color': 'magenta'    , 'marker': 'o', 'markersize': 8  * self.pointScale}
    
    def GetMemberColor(self, internal, maxVal, minVal):
        cmapVal = (internal - minVal) / (maxVal - minVal)
        zeroVal = -minVal / (maxVal - minVal)
        if cmapVal < zeroVal:
            redRatio  = max(0.25, zeroVal - cmapVal)
            color = redRatio * np.array([1., 0., 0.]) + (1 - redRatio) * np.array([1., 1., 1.])
        else:
            blueRatio = max(0.25, cmapVal - zeroVal)
            color = blueRatio * np.array([0., 0., 1.]) + (1 - blueRatio) * np.array([1., 1., 1.])
        
        return color


