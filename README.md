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

![Show](./plot/bar-6_plot_0.png)

## Content (under maintenance)

1. **Installaltion**
    - [Install](#Install)
    - [Update log](#Update-log)
    - [Time consuming](#Time-consuming)
2. **Quick start**
    - [Basic example](./detail/how_to_use.md#Basic-example)
    - [Truss object](./detail/how_to_use.md#Truss-object)
    - [Member object](./detail/how_to_use.md#Member-object)
3. **Combine with JSON**
    - [Example](./detail/combine_with_JSON.md#Example)
    - [Embed in Web APP](./detail/combine_with_JSON.md#Embed-in-Web-APP)
    - [Format of JSON](./detail/combine_with_JSON.md#Format-of-JSON)
4. **Plot your truss**
    - [Example code](./detail/plot_your_truss.md#Example-code)
    - [Example figures](./detail/plot_your_truss.md#Example-figures)
5. **Truss optimization**
    - [Introduction](./detail/truss_optimization.md#Introduction)
    - [Gene](./detail/truss_optimization.md#Gene-data-structure)
    - [Fitness function](./detail/truss_optimization.md#Fitness-function)
    - [Crossover](./detail/truss_optimization.md#Crossover)
    - [Evolution policy](./detail/truss_optimization.md#Evolution-policy)
    - [Example](./detail/truss_optimization.md#Example)
    - [GA object](./detail/truss_optimization.md#GA-object)
    - [Customization](./detail/truss_optimization.md#Customization)

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

> More details is in [Truss optimization](./detail/truss_optimization.md)

Besides GA, there are some new useful methods in the `Truss` object:

```python
class Truss:

    ...

    # Check whether all internal forces are in allowable range or not:
    def IsInternalStressAllowed(self, limit, isGetSumViolation=False) -> tuple[bool, dict | float]: 
        ...

    # Check whether all internal displacements are in allowable range or not:
    def IsDisplacementAllowed(self, limit, isGetSumViolation=False) -> tuple[bool, dict | float]:
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
- **`47-bar truss`**&ensp; : 0.00253(s)
- **`72-bar truss`**&ensp; : 0.00323(s)
- **`120-bar truss`** : 0.00557(s)
- **`942-bar truss`** : 0.05253(s)

Testing on :

```text
CPU: Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz
RAM: 8GB DDR4 * 2
```

---

## Enjoy 😎 !
