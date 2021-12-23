def TestTimeConsuming():
    from slientruss3d.truss import Truss

    # Global variables 
    TEST_FILE_NUMBER = 120
    TEST_LOAD_CASE   = 0
    TEST_INPUT_FILE  = f"./data/bar-{TEST_FILE_NUMBER}_input_{TEST_LOAD_CASE}.json"
    TRUSS_DIMENSION  = 3
    TEST_TIME_NUMBER = 30

    # Truss object and read .json:
    truss = Truss(dim=TRUSS_DIMENSION)
    truss.LoadFromJSON(TEST_INPUT_FILE)

    # Do direct stiffness method:
    import time
    ts = []
    for _ in range(TEST_TIME_NUMBER):
        t0 = time.time()
        truss.Solve()
        ts.append(time.time() - t0)

    mean = sum(ts) / len(ts)
    print(f"Time for structural analysis = {mean}(s)")
    return mean


def TestPlot():
    from slientruss3d.truss import Truss
    from slientruss3d.plot  import TrussPlotter

    # Global variables 
    TEST_FILE_NUMBER        = 25
    TEST_LOAD_CASE          = 0
    TEST_INPUT_FILE         = f"./data/bar-{TEST_FILE_NUMBER}_output_{TEST_LOAD_CASE}.json"
    TEST_PLOT_SAVE_PATH     = f"./plot/bar-{TEST_FILE_NUMBER}_plot_{TEST_LOAD_CASE}.png"
    TRUSS_DIMENSION         = 3
    IS_EQUAL_AXIS           = True
    IS_SAVE_PLOT            = False
    MAX_SCALED_DISPLACEMENT = 15 
    MAX_SCALED_FORCE        = 50   
    POINT_SIZE_SCALE_FACTOR = 1
    ARROW_SIZE_SCALE_FACTOR = 1

    # Truss object:
    truss = Truss(dim=TRUSS_DIMENSION)

    # You could directly read the output .json file.
    truss.LoadFromJSON(TEST_INPUT_FILE, isOutputFile=True)

    # Show or save the structural analysis result figure:
    TrussPlotter(truss,
                 isEqualAxis=IS_EQUAL_AXIS,
                 maxScaledDisplace=MAX_SCALED_DISPLACEMENT, 
                 maxScaledForce=MAX_SCALED_FORCE,
                 pointScale=POINT_SIZE_SCALE_FACTOR,
                 arrowScale=ARROW_SIZE_SCALE_FACTOR).Plot(IS_SAVE_PLOT, TEST_PLOT_SAVE_PATH)


def TestExample():
    from slientruss3d.truss import Truss, Member
    from slientruss3d.type  import SupportType, MemberType
    from slientruss3d.plot  import TrussPlotter

    # -------------------- Global variables --------------------
    # Files settings:
    TEST_OUTPUT_FILE        = f"./data/test_output.json"
    TEST_PLOT_SAVE_PATH     = f"./plot/test_plot.png"

    # Some settings:
    TRUSS_DIMENSION         = 3
    IS_PLOT_TRUSS           = True
    IS_SAVE_PLOT            = False
    
    # Plot layout settings:
    IS_EQUAL_AXIS           = True   # Whether to use actual aspect ratio in the truss figure or not.
    MAX_SCALED_DISPLACEMENT = 15     # Scale the max value of all dimensions of displacements.
    MAX_SCALED_FORCE        = 50     # Scale the max value of all dimensions of force arrows.
    POINT_SIZE_SCALE_FACTOR = 1      # Scale the default size of joint point in the truss figure.
    ARROW_SIZE_SCALE_FACTOR = 1      # Scale the default size of force arrow in the truss figure.
    # ----------------------------------------------------------

    # Truss object:
    truss = Truss(dim=TRUSS_DIMENSION)

    # Read data in this [.py]:
    joints     = [(0, 0, 0), (360, 0, 0), (360, 180, 0), (0, 200, 0), (120, 100, 180)]
    supports   = [SupportType.PIN, SupportType.ROLLER_Z, SupportType.PIN, SupportType.PIN, SupportType.NO]
    forces     = [(1, (0, 100000, 0))]
    members    = [(0, 4), (1, 4), (2, 4), (3, 4), (1, 2)]
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


def TestLoadFromJSON():
    from slientruss3d.truss import Truss
    from slientruss3d.plot  import TrussPlotter

    # -------------------- Global variables --------------------
    # Files settings:
    TEST_FILE_NUMBER        = 10
    TEST_LOAD_CASE          = 0
    TEST_INPUT_FILE         = f"./data/bar-{TEST_FILE_NUMBER}_input_{TEST_LOAD_CASE}.json"
    TEST_OUTPUT_FILE        = f"./data/bar-{TEST_FILE_NUMBER}_output_{TEST_LOAD_CASE}.json"
    TEST_PLOT_SAVE_PATH     = f"./plot/bar-{TEST_FILE_NUMBER}_plot_{TEST_LOAD_CASE}.png"

    # Some settings:
    TRUSS_DIMENSION         = 2
    IS_PLOT_TRUSS           = True
    IS_SAVE_PLOT            = False
    
    # Plot layout settings:
    IS_EQUAL_AXIS           = True   # Whether to use actual aspect ratio in the truss figure or not.
    MAX_SCALED_DISPLACEMENT = 10     # Scale the max value of all dimensions of displacements.
    MAX_SCALED_FORCE        = 50     # Scale the max value of all dimensions of force arrows.
    POINT_SIZE_SCALE_FACTOR = 1      # Scale the default size of joint point in the truss figure.
    ARROW_SIZE_SCALE_FACTOR = 1      # Scale the default size of force arrow in the truss figure.
    # ----------------------------------------------------------

    # Truss object:
    truss = Truss(dim=TRUSS_DIMENSION)

    # Read data in [.json]:
    truss.LoadFromJSON(TEST_INPUT_FILE)

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


def TestGA():
    import random
    from slientruss3d.truss import Truss
    from slientruss3d.type  import MemberType
    from slientruss3d.ga import GA

    allowStress     = 30000.
    allowDisplace   = 10.
    memberTypeList  = [MemberType(inch, random.uniform(1e7, 3e7), random.uniform(0.1, 1.0)) for inch in range(1, 21)]

    truss = Truss(3)
    truss.LoadFromJSON('./data/bar-120_input_0.json')

    ga = GA(truss, memberTypeList, allowStress, allowDisplace, nIteration=None, nPatience=50)
    minGene, (fitness, isInternalAllowed, isDisplaceAllowed), finalPop, bestFitnessHistory = ga.Evolve()

    truss.SetMemberTypes(ga.TranslateGene(minGene))
    truss.Solve()
    truss.DumpIntoJSON(f'bar-120_ga_0.json')


if __name__ == '__main__':
    
    TestGA()
    