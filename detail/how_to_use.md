# Quick start

## Basic example

The following is the example code.  

- You could decide to either just type all the data about the truss in `.py` file or read the data in `.json` file. As for .json file, we will discuss it later.
- If you want to do structural analysis on 2D truss, just switch the dimension of truss by changing the value of variable `TRUSS_DIMENSION` (Only can be **2** or **3**).
- By the way, you could use `slientruss3d.plot.TrussPlotter` to plot the result of structural analysis for your truss. We will discuss its details in [Here](./plot_your_truss.md) !

```python
from slientruss3d.truss import Truss, Member
from slientruss3d.type  import SupportType, MemberType


def TestExample():
    # -------------------- Global variables --------------------
    # Files settings:
    TEST_OUTPUT_FILE    = f"./test_output.json"
    TEST_PLOT_SAVE_PATH = f"./test_plot.png"

    # Some settings:
    TRUSS_DIMENSION     = 3
    # ----------------------------------------------------------

    # Truss object:
    truss = Truss(dim=TRUSS_DIMENSION)

    # Truss settings:
    joints     = [(0, 0, 0), (360, 0, 0), (360, 180, 0), (0, 200, 0), (120, 100, 180)]
    supports   = [SupportType.PIN, SupportType.ROLLER_Z, SupportType.PIN, SupportType.PIN, SupportType.NO]
    forces     = [(1, (0, -10000, 5000))]
    members    = [(0, 4), (1, 4), (2, 4), (3, 4), (1, 2), (1, 3)]
    memberType = MemberType(1, 1e7, 1)

    # Read data in this [.py]:
    for i, (joint, support) in enumerate(zip(joints, supports)):
        truss.AddNewJoint(i, joint, support)
        
    for i, force in forces:
        truss.AddExternalForce(i, force)
    
    for i, (jointID0, jointID1) in enumerate(members):
        truss.AddNewMember(i, jointID0, jointID1, memberType)

    # Do direct stiffness method:
    displace, internal, external = truss.Solve()

    # Dump all the structural analysis results into a .json file:
    truss.DumpIntoJSON(TEST_OUTPUT_FILE)
    
    return displace, internal, external

```

---

## Truss

(Not every method or property is listed here)

### Constructor

```python
Truss(dim)
```

- **`dim`** : Dimension of the truss (only can be `2` or `3`).

<br/>

### Define a new joint

```python
Truss.AddNewJoint(jointID, vector, supportType=SupportType.NO) -> None
```

- **`jointID`** : ID number of the joint.
- **`vector`** : Position of each joints in the truss.
- **`supportType`** : Support type of the joint. The following is the options of support type in slientruss3d:

    >- _SupportType.NO_ &ensp;&emsp;&emsp;&emsp; **(not a support)**
    >- _SupportType.PIN_
    >- _SupportType.ROLLER_X_
    >- _SupportType.ROLLER_Y_
    >- _SupportType.ROLLER_Z_ &emsp;**(only in 3d truss)**

<br/>

### Define a new load

```python
Truss.AddExternalForce(jointID, vector) -> None
```

- **`jointID`** : ID number of the joint.
- **`vector`** : Force vector of each joints in the truss.

<br/>

### Define a new member

```python
Truss.AddNewMember(memberID, jointID0, jointID1, memberType=MemberType()) -> None
```

- **`memberID`** : ID number of the member.
- **`jointID0`** : ID number of the first joint of this member.
- **`jointID1`** : ID number of the second joint of this member.
- **`memberType`** : Member type which contain the information about `cross-sectional area`, `Young's modulus`, `density` of this member.

Here is the detail of class `MemberType`:

```python
class MemberType:
    def __init__(self, a=1., e=1., density=1.):
        self.a       = float(a)
        self.e       = float(e)
        self.density = float(density)
    
    def __repr__(self):
        return f"MemberType(a={self.a}, e={self.e}, density={self.density})"
    
    def Set(other):
        self.a, self.e, self.density = other.a, other.e, other.density
    
    def Serialize(self):
        return [self.a, self.e, self.density]
    
    def Copy(self):
        return MemberType(self.a, self.e, self.density)
```

<br/>

### Get assembled stiffness matrix (K)

```python
Truss.GetKMatrix() -> numpy.array
```

- It will return a numpy array which is the assembled K matrix.

<br/>

### Do structural analysis

```python
Truss.Solve() -> None
```

- Do the structral analysis of your truss by `direct stiffness method`. After that, all the `internal force (not stress!)` of each member, `displacement` and `total force` at each joint will solved and stored in the Truss object. You could get them with some getters defined in Truss.

> &ensp;&ensp; As said in [Description](../README.md#Description), slientruss3d is made for **`stable`** truss analysis. So once you call the method `Truss.Solve()`, it will check whether your truss is stable or not with the property **`Truss.isStable`**. If your truss is not stable, an exception `TrussNotStableError` will be raised.

<br/>


### Get internal stress

```python
Truss.GetInternalStresses() -> dict[int, float]
```

- Get inetrnal stress at each member. It returns a dictionary whose key is `member ID` and value is `stress`.
- Note that if you haven't done structural analysis yet, this method will return `None`.

<br/>


### Get internal force

```python
Truss.GetInternalForces() -> dict[int, float]
```

- Get inetrnal force at each member. It returns a dictionary whose key is `member ID` and value is `force magnitude`.
- Note that if you haven't done structural analysis yet, this method will return `None`.

<br/>


### Get joint displacement

```python
Truss.GetDisplacements() -> dict[int, numpy.array]
```

- Get displacement at each joint. It returns a dictionary whose key is `joint ID` and value is `displacement vector`.
- Note that if you haven't done structural analysis yet, this method will return `None`.

<br/>

### Load truss data from JSON file

```python
Truss.LoadFromJSON(path=None, isOutputFile=False, data=None) -> Truss
```

- **`path`** : Filename of the JSON file.
- **`isOutputFile`** : Whether the JSON file or dictionary data contains the result of structural analysis.
- **`data`** : Directly assign a `dictionary` whose format is the same as [Format of JSON](./combine_with_JSON.md#Format-of-JSON). If it's not none, do not assgin any value to the argument `path`.

<br/>

### Save the structural analysis result in a JSON file

```python
Truss.DumpIntoJSON(path) -> None
```

- **`path`** : Filename of the JSON in which you want to store the result of structural analysis.

    > More about the utility of JSON will be introduced in [Combine with JSON](./combine_with_JSON.md) !

<br/>

### Serialize the truss

```python
Truss.Serialize() -> dict
```

- Return a dictionary which contains all the information about the truss.
    > The format is the same as [Format of JSON](./combine_with_JSON.md#Format-of-JSON).

<br/>

### Check whether every stress is allowable

```python
Truss.IsInternalStressAllowed(limit, isGetSumViolation=False) -> tuple[bool, dict | float]
```

- **`limit`** : Allowable stress.
- **`isGetSumViolation`** : Sum of the exceeding quantities of members that violate allowable stress.

&ensp; If the parameter `isGetSumViolation` is True, then the method returns

>1. **boolean** : indicates whether the truss violates the allowable limit or not.
>2. **float**&ensp;&ensp;&ensp; : sum of absolute values of exceeding stresses or displacements.  

<br/>

### Check whether every displacement is allowable

```python
Truss.IsDisplacementAllowed(limit, isGetSumViolation=False) -> tuple[bool, dict | float]
```

- **`limit`** : Allowable displacement.
- **`isGetSumViolation`** : Sum of the exceeding quantities of members that violate allowable displacement.

&ensp; If the parameter `isGetSumViolation` is True, then the method returns

>1. **boolean** : indicates whether the truss violates the allowable limit or not.
>2. **float**&ensp;&ensp;&ensp; : sum of absolute values of exceeding stresses or displacements. 

<br/>

### Copy the truss

```python
Truss.Copy() -> Truss
```

<br/>

### Some useful properties

- Weight of the truss.

```python
Truss.weight : float
```

- Whether the truss is stable or not ?

```python
Truss.isStable : bool
```

- Whether the truss has been done structral analysis or not ?

```python
Truss.isSolved : bool
```

- Number of joints.

```python
Truss.nJoint : int
```

- Number of members.

```python
Truss.nMember : int
```

- Number of loads.

```python
Truss.nForce : int
```

- Number of supports (support type is **not** _`SupportType.NO`_).

```python
Truss.nSupport : int
```

- Number of resistances.

```python
Truss.nResistance : int
```

- Dimension of the truss

```python
Truss.dim : int
```

<br/>

---

## Member

### Constructor

```python
Member(joint0, joint1, dim=3, memberType=MemberType()) -> None
```

<br/>

### Check whether the member is tension strss or not

``` python
Member.IsTension(forceVec) -> bool
```

- **`forceVec`** : The internal force vector on `joint1`.

<br/>

### Serialize the member

```python
Member.Serialize() -> dict
```

- Return a dictionary which contains all the information about the member. The following is its format:

```python
{
    "joint0"    : list[float],  # Position of joint0
    "joint1"    : list[float],  # Position of joint1
    "memberType": list[float]   # Cross-sectional area, Young's modulus, density
} 
```

<br/>

### Copy the member

```python
Member.Copy() -> Member
```

<br/>

### Some useful properties

- Weight of the member.

```python
Member.weight : float
```

- Length of the member.

```python
Member.length : float
```

- Cross-sectional area.

```python
Member.a : float
```

- Young's modulus.

```python
Member.e : float
```

- Density.

```python
Member.density : float
```

- Member type. (Has both getter and setter)

```python
Member.memberType : MemberType
```

- Cosine values of every axis.

```python
Member.cosines : list[float]
```

- E * A / L.

```python
Member.k : float
```

- Stiffness matrix (K).

```python
Member.matK : numpy.array
```

- Dimension of the member.

```python
Member.dim : int
```
