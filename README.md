# **slientruss3d** : Python for stable truss analysis tool
[![Python](https://img.shields.io/pypi/pyversions/slientruss3d)](https://pypi.org/project/slientruss3d/)
[![Version](https://img.shields.io/pypi/v/slientruss3d)](https://pypi.org/project/slientruss3d/)
[![GitHub release](https://img.shields.io/github/release/leo27945875/Python_Stable_3D_Truss_Analysis.svg)](https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis/releases)
[![License](https://img.shields.io/github/license/leo27945875/Python_Stable_3D_Truss_Analysis)](https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis/blob/master/LICENSE.txt)

---

## Desciption

**`slientruss3d`** is a python package which can solve the resistances, internal forces and joint dispalcements in a stable 2D or 3D truss by `direct stiffness method`.This repo is writen by  :

```text
Taiwan                                          (臺灣)
Department of Civil Engineering                 (土木工程學系)
National Yang Ming Chiao Tung University (NYCU) (國立陽明交通大學)
Shih-Chi Cheng                                  (鄭適其)
```

---

## How to use ?

First, check your python version:

```text
Python >= 3.9.0
```

Second, download the **`slientruss3d`** package:

```text
pip install slientruss3d 
```

The following is one of the example codes in example.py. 
You could decide to either just type all the data about the truss in `.py` file or read the data in `.json` file. As for .json file, we will discuss later.
If you want to do structural analysis on 2D truss, just switch the dimension of truss by changing the value of variable `TRUSS_DIMENSION` (Only can be **2** or **3**).

```python
from slientruss3d.truss import Truss, Member
from slientruss3d.type  import SupportType, MemberType
from slientruss3d.plot  import TrussPlotter


def TestExample():
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
    supports   = [SupportType.PIN, SupportType.PIN, SupportType.PIN, SupportType.PIN, SupportType.NO]
    forces     = [(4, (0, 0, -10000))]
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

```

---

## Format of JSON

See the example code in example.py :

```python
def TestLoadFromJSON():
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

```

The `input` data of truss in the .json file must follow this format :  
( **support_type** can be one of ["NO", "PIN", "ROLLER_X", "ROLLER_Y", "ROLLER_Z"], and "ROLLER_Z" only can be used in 3D truss.)

```json
{
    // Joints 
    // {"joint_ID" : [positionX, positionY, positionZ, support_type]}
    "joint": {
        "0": [[0 , 0 , 0 ], "PIN"     ],  
        "1": [[36, 0 , 0 ], "PIN"     ],
        "2": [[36, 18, 0 ], "ROLLER_Z"],
        "3": [[0 , 20, 0 ], "PIN"     ],
        "4": [[12, 10, 18], "NO"      ]
    },

    // External forces
    // {"joint_ID" : [forceX, forceY, forceZ]}
    "force": {
        "4": [0, 7000, -10000]
    },

    // Members
    // {"member_ID" : [[joint_ID_0, joint_ID_1], [area, Young's modulus, density]]}
    "member": {
        "0": [[0, 4], [1, 1e7, 1]],
        "1": [[1, 4], [1, 1e7, 1]],
        "2": [[2, 4], [1, 1e6, 1]],
        "3": [[3, 4], [1, 1e7, 1]],
        "4": [[0, 2], [1, 1e6, 1]],
        "5": [[1, 2], [1, 1e7, 1]]
    }
}
```

And the format of `ouput` .json file will be like :

```json
{
    // Joints
    "joint": {
        "0": [[0 , 0 , 0 ], "PIN"     ], 
        "1": [[36, 0 , 0 ], "PIN"     ], 
        "2": [[36, 18, 0 ], "ROLLER_Z"], 
        "3": [[0 , 20, 0 ], "PIN"     ], 
        "4": [[12, 10, 18], "NO"      ]
    }, 

    // External forces
    "force": {
        "4": [0, 7000, -10000]
    }, 

    // Members
    "member": {
        "0": [[0, 4], [1, 10000000, 1]], 
        "1": [[1, 4], [1, 10000000, 1]], 
        "2": [[2, 4], [1, 1000000 , 1]], 
        "3": [[3, 4], [1, 10000000, 1]], 
        "4": [[0, 2], [1, 1000000 , 1]], 
        "5": [[1, 2], [1, 10000000, 1]]
    }, 

    // Solved displacement of each joint
    "displace": {
        "0": [0                   ,  0                     ,  0                   ], 
        "1": [0                   ,  0                     ,  0                   ], 
        "2": [0.03134498120304671 , -0.00018634976892802215,  0                   ], 
        "3": [0                   ,  0                     ,  0                   ], 
        "4": [0.022796692569021636,  0.05676049798868429   , -0.029124752172511904]
    }, 

    // External forces with solved resistances
    "external": {
        "0": [-3430.530131923594 , -2651.7198111274147, -4214.046353245278 ],
        "1": [-3823.2785480177026,  1696.5603777451659,  2867.4589110132774],
        "2": [ 0                 ,  0                 ,  465.8744223200557 ],
        "3": [ 7253.808679941296 , -6044.840566617749 ,  10880.713019911946],
        "4": [ 0                 ,  7000              , -10000             ]
    },

    // Solved internal force in each member (Tension is positive, Compression is negative)
    "internal": {
        "0":  5579.573091723386 , 
        "1": -5037.6118087489085, 
        "2": -803.590657623974  , 
        "3": -14406.517749362636, 
        "4":  694.4845848573933 , 
        "5": -103.52764940445674
    }, 

    // The total weight of this truss (note that the default density is 1.0)
    "weight": 168.585850740452
}
```

---

## Time consuming

The following are time consuming tests for doing structural analysis for each truss (Each testing runs for 30 times and takes average !).

- **`6-bar truss`**&ensp;&ensp; : 0.00043(s)
- **`10-bar truss`**&ensp; : 0.00063(s)
- **`25-bar truss`**&ensp; : 0.00176(s)
- **`72-bar truss`**&ensp; : 0.00443(s)
- **`120-bar truss`** : 0.00728(s)
- **`942-bar truss`** : 0.07440(s)

Testing on :

```text
CPU: Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz
RAM: 8GB DDR4 * 2
```

---

## Result figures

You could use `slientruss3d.plot.TrussPlotter` to plot the result of structural analysis for your truss. 
See the following example in example.py:

```python
from slientruss3d.truss import Truss
from slientruss3d.plot  import TrussPlotter


def TestPlot():
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
```

- **`Green Arrow`** &ensp;&ensp;: Resistance
- **`Purple Arrow`** &ensp;: External Force
- **`Black Line`** &ensp;&ensp;&ensp;: Member
- **`Blue Dashline`** : Displaced member with tension
- **`Red Dashline`** &ensp;: Displaced member with compression
- **`Pink Circle`** &ensp;&ensp;: Joint
- **`Blue Circle`** &ensp;&ensp;: Roller
- **`Blue Triangle`** : Pin

<br/>

**Input** : `./data/bar-6_output_0.json`
![0](./plot/bar-6_plot_0.png)

<br/>

**Input** : `./data/bar-10_output_0.json`
![1](./plot/bar-10_plot_0.png)

<br/>

**Input** : `./data/bar-25_output_0.json`
![1](./plot/bar-25_plot_0.png)

**Input** : `./data/bar-47_output_0.json`
![1](./plot/bar-47_plot_0.png)

<br/>

**Input** : `./data/bar-72_output_1.json`
![1](./plot/bar-72_plot_1.png)

<br/>

**Input** : `./data/bar-120_output_0.json`
![1](./plot/bar-120_plot_0.png)

<br/>

**Input** : `./data/bar-942_output_0.json`
![1](./plot/bar-942_plot_0.png)

## Enjoy 😎 !