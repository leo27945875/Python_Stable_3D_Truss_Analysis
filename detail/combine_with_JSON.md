# Combine with JSON

## Example

See the example code :

```python
from slientruss3d.truss import Truss


def TestLoadFromJSON():
    # -------------------- Global variables --------------------
    # Files settings:
    TEST_FILE_NUMBER = 10
    TEST_LOAD_CASE   = 0
    TEST_INPUT_FILE  = f"./data/bar-{TEST_FILE_NUMBER}_input_{TEST_LOAD_CASE}.json"
    TEST_OUTPUT_FILE = f"./data/bar-{TEST_FILE_NUMBER}_output_{TEST_LOAD_CASE}.json"

    # Truss dimension setting:
    TRUSS_DIMENSION  = 2
    # ----------------------------------------------------------

    # Truss object:
    truss = Truss(dim=TRUSS_DIMENSION)

    # Read data in [.json]:
    truss.LoadFromJSON(TEST_INPUT_FILE)

    # Do direct stiffness method:
    truss.Solve()

    # Dump all the structural analysis results into a .json file:
    truss.DumpIntoJSON(TEST_OUTPUT_FILE)
```

---

## Embed in Web APP

You could also use the parameter **`data`** in method `LoadFromJSON` to assign a dictionary whose format is the same as our JSON:

```python
## ...... something to do ...... ##

from flask import request

truss.LoadFromJSON(data=request.json)

## ...... something to do ...... ##
```

Or make an JSON response to the client with the method **`Truss.Serialize()`**:

```python
## ...... something to do ...... ##

from flask import make_response, jsonify

@app.route("/....")
def Response():
    ## ...... something to do ...... ##
    return make_response(jsonify(truss.Serialize()))

## ...... something to do ...... ##
```

> There is also a method serialization method **`Member.Serialize()`** in class Member !

---

## Format of JSON

The `input` data of truss in the .json file must follow this format :  
( **support_type** can be one of ["NO", "PIN", "ROLLER_X", "ROLLER_Y", "ROLLER_Z"], and "ROLLER_Z" only can be used in 3D truss.)

```json
{
    // Joints 
    // [ [[positionX, positionY, positionZ], support_type] ]
    "joint": [
        [[0 , 0 , 0 ], "PIN"     ],  
        [[36, 0 , 0 ], "PIN"     ],
        [[36, 18, 0 ], "ROLLER_Z"],
        [[0 , 20, 0 ], "PIN"     ],
        [[12, 10, 18], "NO"      ]
    ],

    // External forces
    // [ [joint_ID, [forceX, forceY, forceZ]] ]
    "force": [
        [4, [0, 7000, -10000]]
    ],

    // Members
    // [ [[joint_ID_0, joint_ID_1], [area, Young's modulus, density]] ]
    "member": [
        [[0, 4], [1, 1e7, 1]],
        [[1, 4], [1, 1e7, 1]],
        [[2, 4], [1, 1e6, 1]],
        [[3, 4], [1, 1e7, 1]],
        [[0, 2], [1, 1e6, 1]],
        [[1, 2], [1, 1e7, 1]]
    ]
}
```

And the format of `ouput` .json file will be like :

```json
{
    // Joints
    "joint": [
        [[0 , 0 , 0 ], "PIN"     ],  
        [[36, 0 , 0 ], "PIN"     ],
        [[36, 18, 0 ], "ROLLER_Z"],
        [[0 , 20, 0 ], "PIN"     ],
        [[12, 10, 18], "NO"      ]
    ],

    // External forces
    "force": [
        [4, [0, 7000, -10000]]
    ],

    // Members
    "member": [
        [[0, 4], [1, 1e7, 1]],
        [[1, 4], [1, 1e7, 1]],
        [[2, 4], [1, 1e6, 1]],
        [[3, 4], [1, 1e7, 1]],
        [[0, 2], [1, 1e6, 1]],
        [[1, 2], [1, 1e7, 1]]
    ],

    // Solved displacement of each joint (only contains non-zero part)
    "displace": [ 
        [2, [0.03134498120304671 , -0.00018634976892802215,  0                   ]], 
        [4, [0.022796692569021636,  0.05676049798868429   , -0.029124752172511904]]
    ], 

    // Total external force at each joint (only contains non-zero part)
    "external": [
        [0, [-3430.530131923594 , -2651.7198111274147, -4214.046353245278 ]],
        [1, [-3823.2785480177026,  1696.5603777451659,  2867.4589110132774]],
        [2, [ 0                 ,  0                 ,  465.8744223200557 ]],
        [3, [ 7253.808679941296 , -6044.840566617749 ,  10880.713019911946]],
        [4, [ 0                 ,  7000              , -10000             ]]
    ],

    // Solved internal force (not stress !) in each member (Tension is positive, Compression is negative, only contains non-zero part)
    "internal": [
        [0,  5579.573091723386 ], 
        [1, -5037.6118087489085], 
        [2, -803.590657623974  ], 
        [3, -14406.517749362636], 
        [4,  694.4845848573933 ], 
        [5, -103.52764940445674]
    ], 

    // The total weight of this truss (note that the default density is 1.0)
    "weight": 168.585850740452
}
```
