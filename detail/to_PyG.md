# Convert Truss to Pytorch-Geometric HeteroData


With the increasing importance of deep learning in the field of truss design, we also provide a solution to let our users convert the `Truss` object to the data structure of `Pytorch-Geometric` conveniently.  
After slientruss3d v2.0.0, you can use **`slientruss3d.data.TrussHeteroDataCreator`** to build heterogeneous graph data (torch_geometric.data.HeteroData).

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
- **`trussSrc`** : The identifier of the input truss. (Can be None, an integer, source JSON filename ... etc)

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