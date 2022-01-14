# **slientruss3d** : Python for stable truss analysis and optimization tool

[![Python](https://img.shields.io/pypi/pyversions/slientruss3d)](https://pypi.org/project/slientruss3d/)
[![Version](https://img.shields.io/pypi/v/slientruss3d)](https://pypi.org/project/slientruss3d/)
[![GitHub release](https://img.shields.io/github/release/leo27945875/Python_Stable_3D_Truss_Analysis.svg)](https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis/releases)
[![Downloads](https://img.shields.io/pypi/dm/slientruss3d?color=red)](https://pypi.org/project/slientruss3d/)
[![License](https://img.shields.io/github/license/leo27945875/Python_Stable_3D_Truss_Analysis)](https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis/blob/master/LICENSE.txt)

---

## Desciption

**`slientruss3d`** is a python package which can solve the resistances, internal forces and joint dispalcements in a stable 2D or 3D truss by `direct stiffness method`. And also can do truss optimization by `Genetic Algorithm (GA)` conveniencely.  
  
This repo is writen by  :

```text
Taiwan                                          (臺灣)
Department of Civil Engineering                 (土木工程學系)
National Yang Ming Chiao Tung University (NYCU) (國立陽明交通大學)
Shih-Chi Cheng                                  (鄭適其)
```

## Content

1. **Quick start**
    - [Install](#Install)
    - [Update log](#Update-log)
2. **Quick start**
    - [Basic example](./detail/how_to_use.md#Basic-example)
    - [Truss object](./detail/how_to_use.md#Truss-object)
    - [Member object](./detail/how_to_use.md#Member-object)
3. **Combine with JSON**
    - [Example](./detail/combine_with_JSON.md#Example)
    - [Embed in Web APP](./detail/combine_with_JSON.md#Embed-in-Web-APP)
    - [Format of JSON](./detail/combine_with_JSON.md#Format-of-JSON)

---

## Install

First, check your python version:

```text
Python must >= 3.9.0
```

Second, download the **`slientruss3d`** package:

```text
pip install slientruss3d 
```

---

## Update log

### New feature in v1.2.x update !

After slientruss3d v1.2.x, you could use **`slientruss3d.ga`** module to do `truss type selection optimization` conveniencely with `Genetic Algorithm (GA)`! Just simply define the topology of the truss and what member types you want to use, and then you could start the optimization.  
The following is the example code of GA:

```python
from slientruss3d.truss import Truss
from slientruss3d.type  import MemberType
from slientruss3d.ga    import GA
import random


def TestGA():
    # Allowable stress and displacement:
    ALLOWABLE_STRESS         = 30000.
    ALLOWABLE_DISPLACEMENT   = 10.

    # Type the member types you want to use here:
    MEMBER_TYPE_LIST = [MemberType(inch, random.uniform(1e7, 3e7), random.uniform(0.1, 1.0)) for inch in range(1, 21)]

    # GA settings:
    MAX_ITERATION      = None  # When [MAX_ITERATION] is None, do infinite iteration until convergence (reach [PATIENCE_ITERATION]).
    PATIENCE_ITERATION = 50

    # Truss object:
    truss = Truss(3)
    truss.LoadFromJSON('./data/bar-120_input_0.json')

    # Do GA:
    ga = GA(truss, MEMBER_TYPE_LIST, ALLOWABLE_STRESS, ALLOWABLE_DISPLACEMENT, nIteration=MAX_ITERATION, nPatience=PATIENCE_ITERATION)
    minGene, (fitness, isInternalAllowed, isDisplaceAllowed), finalPop, bestFitnessHistory = ga.Evolve()

    # Translate optimal gene to member types:
    truss.SetMemberTypes(ga.TranslateGene(minGene))

    # Save result:
    truss.Solve()
    truss.DumpIntoJSON(f'bar-120_ga_0.json')
```

Besides GA, there are some new useful methods in the `Truss` object:

```python
class Truss:

    ...

    # Check whether all internal forces are in allowable range or not:
    def IsInternalStressAllowed(self, limit, isGetSumViolation=False) -> bool, dict | float: 
        ...

    # Check whether all internal displacements are in allowable range or not:
    def IsDisplacementAllowed(self, limit, isGetSumViolation=False) -> bool, dict | float:
        ...

```

If the parameter `isGetSumViolation` is True, then the method returns

>1. **boolean** : indicates whether the truss violates the allowable limit or not.
>2. **float**&ensp;&ensp;&ensp; : sum of absolute values of exceeding stresses or displacements.  

Otherwise, it returns

>1. **boolean**&ensp;&ensp; : indicates whether the truss violates the allowable limit or not.
>2. **dictionary** : contains the information of each node or member which violates the allowable limit and its absolute value of exceeding quantity.

---

## Time consuming

The following are time consuming tests for doing structural analysis for each truss (Each testing runs for 30 times and takes average !).

- **`6-bar truss`**&ensp;&ensp; : 0.00037(s)
- **`10-bar truss`**&ensp; : 0.00050(s)
- **`25-bar truss`**&ensp; : 0.00126(s)
- **`47-bar truss`**&ensp; : 0.00203(s)
- **`72-bar truss`**&ensp; : 0.00323(s)
- **`120-bar truss`** : 0.00557(s)
- **`942-bar truss`** : 0.05253(s)

Testing on :

```text
CPU: Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz
RAM: 8GB DDR4 * 2
```

---

## Result figures

You could use `slientruss3d.plot.TrussPlotter` to plot the result of structural analysis for your truss. 
See the following example:

```python
from slientruss3d.truss import Truss
from slientruss3d.plot  import TrussPlotter


def TestPlot():
    # -------------------- Global variables --------------------
    # Files settings:
    TEST_FILE_NUMBER        = 25
    TEST_LOAD_CASE          = 0
    TEST_INPUT_FILE         = f"./data/bar-{TEST_FILE_NUMBER}_output_{TEST_LOAD_CASE}.json"
    TEST_PLOT_SAVE_PATH     = f"./plot/bar-{TEST_FILE_NUMBER}_plot_{TEST_LOAD_CASE}.png"

    # Truss dimension setting:
    TRUSS_DIMENSION         = 3

    # Figure layout settings:
    IS_SAVE_PLOT            = False   # Whether to save truss figure or not.
    IS_EQUAL_AXIS           = True    # Whether to use actual aspect ratio in the truss figure or not.
    MAX_SCALED_DISPLACEMENT = 15      # Scale the max value of all dimensions of displacements.
    MAX_SCALED_FORCE        = 50      # Scale the max value of all dimensions of force arrows.
    POINT_SIZE_SCALE_FACTOR = 1       # Scale the default size of joint point in the truss figure.
    ARROW_SIZE_SCALE_FACTOR = 1       # Scale the default size of force arrow in the truss figure.
    # ----------------------------------------------------------

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