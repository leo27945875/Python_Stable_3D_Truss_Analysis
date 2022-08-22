# Convert Truss to Pytorch-Geometric HeteroData


With the increasing importance of graph deep learning in the field of truss design, we also provide a solution to let our users convert the `Truss` object to the data structure of `Pytorch-Geometric` conveniently.  
After slientruss3d v2.0.0, you can use **`slientruss3d.data.TrussHeteroDataCreator`** to build heterogeneous graph data (torch_geometric.data.HeteroData).

## Installation

[Install PyTorch Geometric](https://pytorch-geometric.readthedocs.io/en/latest/notes/installation.html)

## How to use it ?

### Constructor

```python
TrussHeteroDataCreator(metapathType: MetapathType, taskType: TaskType) -> None
```

- **`metapathType`** : Whether to use impicit connection of the bipartite graph representation of the truss.

    >- _MetapathType.USE_IMPLICIT_
    >- _MetapathType.NO_IMPLICIT_

- **`taskType`** : Type of your task. It'll affect the fields of the HeteroData.

    >- _TaskType.OPTIMIZATION_  
    >- _TaskType.REGRESSION_

( Both `MetapathType` and `TaskType` are in `slientruss3d.type` module. )

<br/>

### Build HeteroData from JSON file

```python
TrussHeteroDataCreator.FromJSON(
    trussJSONFile, trussDim, forceScale, displaceScale, positionScale, 
    usedMemberTypes=None, 
    fixedMemberType=MemberType(1., 1e7, 0.1), 
    isUseFixed=True, 
    isOutputFile=False
) -> torch_geometric.data.HeteroData
```

- **`trussJSONFile`** : JSON file.
- **`trussDim`** : Dimension of the truss.
- **`forceScale`** : All the external force magnitudes in HeteroData will be divided by this value.
- **`displaceScale`** : All the displacement magnitudes in HeteroData will be divided by this value.
- **`positionScale`** : All the position ( x, y, (z) ) magnitudes in HeteroData will be divided by this value.
- **`usedMemberTypes`** : If you want to do regression or imiation-learning task, please provide the list of used MemberTypes.
- **`fixedMemberType`** : This parameter is used to get prior stress and displacement of the truss.
- **`isUseFixed`** : Whether to include prior stress and displacement in HeteroData or not.
- **`isOutputFile`** : Whether the JSON file is an output file or not.

<br/>

### Build HeteroData from Truss object

```python
TrussHeteroDataCreator.FromTruss(
    truss, forceScale, displaceScale, positionScale, 
    usedMemberTypes=None, 
    fixedMemberType=MemberType(1., 1e7, 0.1), 
    isUseFixed=True, 
    trussSrc=None
) -> torch_geometric.data.HeteroData
```

- **`truss`** : Truss object.
- **`forceScale`** : All the external force magnitudes in HeteroData will be divided by this value.
- **`displaceScale`** : All the displacement magnitudes in HeteroData will be divided by this value.
- **`positionScale`** : All the position ( x, y, (z) ) magnitudes in HeteroData will be divided by this value.
- **`usedMemberTypes`** : If you want to do regression or imiation-learning task, please provide the list of used MemberTypes.
- **`fixedMemberType`** : This parameter is used to get prior stress and displacement of the truss.
- **`isUseFixed`** : Whether to include prior stress and displacement in HeteroData or not.
- **`trussSrc`** : An identifier of the input truss. (Can be None, an integer, source JSON filename ... etc)

<br/>

### Add dense edges

```python
TrussHeteroDataCreator.AddDenseEdges(graphData: torch_geometric.data.HeteroData) -> torch_geometric.data.HeteroData
```

> Note that this method will modify the input data directly.

- **`graphData`** : HeteroData.

### Add master node

```python
TrussHeteroDataCreator.AddMasterNode(graphData: torch_geometric.data.HeteroData, embeddingDim=1, fillValue=1.) -> torch_geometric.data.HeteroData
```

> Note that this method will modify the input data directly.

- **`graphData`** : HeteroData.
- **`embeddingDim`** : Dimension of the initial master node embedding.
- **`fillValue`** : Initial value of all the elements in master node embedding.

### Some useful properties

- Origin Truss object.

```python
TrussHeteroDataCreator.truss : Truss
```

- Source of the origin truss. You could use it to find the origin Truss object from a batch of HeteroData.

```python
TrussHeteroDataCreator.source : Any
```

- Mapping from the indices of HeteroData["joint"] to jointIDs in Truss object.

```python
TrussHeteroDataCreator.jointIndexToID : list[int]
```

- Mapping from the indices of HeteroData["member"] to memberIDs in Truss object.

```python
TrussHeteroDataCreator.memberIndexToID : list[int]
```

## Fields in HeteroData

### For optimization task (TaskType.OPTIMIZATION)

- X data :
    - Joint :
        - If `isUseFix` is `True` :
            > \[ Position_X, Position_Y, Position_Z, Force_X, Force_Y, Force_Z, Prior_Displace_X, Prior_Displace_Y, Prior_Displace_Z, Is_Support \]
        - If `isUseFix` is `False` :
            > \[ Position_X, Position_Y, Position_Z, Force_X, Force_Y, Force_Z, Is_Support \]
    - Member :
        - If `isUseFix` is `True` :
            > \[ Centroid_X, Centroid_Y, Centroid_Z, sin(Angle_Z_Axis), cos(Angle_Z_Axis), sin(Angle_X_Axis), cos(Angle_X_Axis), Member_Length, Prior_Internal_Force \]
        - If `isUseFix` is `False` :
            > \[ Centroid_X, Centroid_Y, Centroid_Z, sin(Angle_Z_Axis), cos(Angle_Z_Axis), sin(Angle_X_Axis), cos(Angle_X_Axis), Member_Length \]
- Y data :
    - Joint :
        > (No data)
    - Member :
        - If `usedMemberTypes` is not None :
            > [Index_of_MemberType_in_`usedMemberTypes`]
        - If `usedMemberTypes` is None :
            > (No data)
- Other :
    - Origin weigth of each Truss :
        > \[ Origin_Weight \]
    - Source of each Truss :
        > \[ Source \]

### For Regression task (TaskType.REGRESSION)

- X data :
    - Joint :
        - If `isUseFix` is `True` :
            > \[ Position_X, Position_Y, Position_Z, Force_X, Force_Y, Force_Z, Prior_Displace_X, Prior_Displace_Y, Prior_Displace_Z, Is_Support \]
        - If `isUseFix` is `False` :
            > \[ Position_X, Position_Y, Position_Z, Force_X, Force_Y, Force_Z, Is_Support \]
    - Member :
        - If `isUseFix` is `True` :
            > \[ Centroid_X, Centroid_Y, Centroid_Z, sin(Angle_Z_Axis), cos(Angle_Z_Axis), sin(Angle_X_Axis), cos(Angle_X_Axis), Member_Length, Prior_Axial_Force, Cross_Sectioal_Area \]
        - If `isUseFix` is `False` :
            > \[ Centroid_X, Centroid_Y, Centroid_Z, sin(Angle_Z_Axis), cos(Angle_Z_Axis), sin(Angle_X_Axis), cos(Angle_X_Axis), Member_Length, Cross_Sectioal_Area \]
- Y data :
    - Joint :
        > \[ Displace_X, Displace_Y, Displace_Z \]
    - Member :
        > \[ Axial_Stress \]
- Other :
    - Origin weigth of each Truss :
        > \[ Origin_Weight \]
    - Source of each Truss :
        > \[ Source \]