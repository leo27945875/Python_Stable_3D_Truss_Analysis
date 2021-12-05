from slientruss3d.truss import Truss, Member
from slientruss3d.type  import SupportType, MemberType
from slientruss3d.plot  import TrussPlotter


def TestExample():
    # -------------------- Global variables --------------------
    # Files settings:
    TEST_FILE_NUMBER        = 25
    TEST_LOAD_CASE          = 0
    TEST_INPUT_FILE         = f"./data/bar-{TEST_FILE_NUMBER}_input_{TEST_LOAD_CASE}.json"
    TEST_OUTPUT_FILE        = f"./data/bar-{TEST_FILE_NUMBER}_output_{TEST_LOAD_CASE}.json"
    TEST_PLOT_SAVE_PATH     = f"./plot/bar-{TEST_FILE_NUMBER}_plot_{TEST_LOAD_CASE}.png"

    # Some settings:
    TRUSS_DIMENSION         = 3
    IS_READ_FROM_JSON       = True
    IS_PLOT_TRUSS           = True
    IS_SAVE_PLOT            = True
    
    # Plot layout settings:
    IS_EQUAL_AXIS           = True   # Whether to use actual aspect ratio in the truss figure or not.
    MAX_SCALED_DISPLACEMENT = 15     # Scale the max value of all dimensions of displacements.
    MAX_SCALED_FORCE        = 50     # Scale the max value of all dimensions of force arrows.
    POINT_SIZE_SCALE_FACTOR = 1      # Scale the default size of joint point in the truss figure.
    ARROW_SIZE_SCALE_FACTOR = 1      # Scale the default size of force arrow in the truss figure.
    # ----------------------------------------------------------

    # Truss object:
    truss = Truss(dim=TRUSS_DIMENSION)

    # Read data in [.json] or in this [.py]:
    if IS_READ_FROM_JSON:
        truss.LoadFromJSON(TEST_INPUT_FILE)
    else:
        joints     = [(0, 0, 0), (36, 0, 0), (36, 18, 0), (0, 20, 0), (12, 10, 18)]
        supports   = [SupportType.PIN, SupportType.PIN, SupportType.PIN, SupportType.PIN, SupportType.NO]
        forces     = [(4, (0, -10000, 0))]
        members    = [(0, 4), (1, 4), (2, 4), (3, 4)]
        memberType = MemberType(1, 1e7, 1)
        
        for i, (joint, support) in enumerate(zip(joints, supports)):
            truss.AddNewJoint(i, joint, support)
            
        for i, force in forces:
            truss.AddExternalForce(i, force)
        
        for i, (jointID0, jointID1) in enumerate(members):
            truss.AddNewMember(i, jointID0, jointID1, Member(joints[jointID0], joints[jointID1], 3, memberType))

    # Do direct stiffness method:
    displace, internal, external = truss.Solve()

    # Dump all the structural analysis results into a .json file:
    truss.DumpIntoJSON(TEST_OUTPUT_FILE)

    # Show or save the structural analysis result figure:
    if IS_PLOT_TRUSS:
        TrussPlotter(truss,
                     isEqualAxis=IS_EQUAL_AXIS,
                     maxScaledDisplace=MAX_SCALED_DISPLACEMENT, 
                     maxScaledForce=MAX_SCALED_FORCE,
                     pointScale=POINT_SIZE_SCALE_FACTOR,
                     arrowScale=ARROW_SIZE_SCALE_FACTOR).Plot(IS_SAVE_PLOT, TEST_PLOT_SAVE_PATH)
    
    return displace, internal, external


if __name__ == '__main__':
    TestExample()