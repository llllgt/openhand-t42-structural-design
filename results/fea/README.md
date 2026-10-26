# Raw finite-element records

Final results are the four `*_p2_*.json` records: two geometries, two mesh sizes, three load cases each. `raw-p2.zip` contains their twelve corresponding NPZ files.

NPZ fields:
- `points`: corner vertex coordinates in mm.
- `tets`: linear tetrahedral geometry connectivity, indexing `points`.
- `triangles`: external boundary triangles, indexing `points`.
- `displacement`: P2 solution sampled at corner nodes, in mm, same order as `points`.
- `element_vm`: volume-integrated average von Mises stress for each element, in MPa. Not nodally extrapolated stress or a local peak.
- `fixed_nodes`: corner node indices on fixed hole walls; additional quadratic edge DOFs are also constrained during the solve.
- `force`: consistent applied forces at all P2 scalar-basis nodes (corners plus edge nodes), components X/Y/Z. It is longer than `points`. The coordinates/order can be reconstructed using the MeshTet/Basis construction in `scripts/analyze.py` and `basis.doflocs[:, basis.split_indices()[0]]`.

`mesh_size_mm` is a Gmsh maximum target; curvature and local features also control actual sizes. Volumes in CAD metrics are exact boundary-representation volumes; FE mesh volumes are polyhedral approximations.

The maximum-displacement statistic samples corner nodes only. The `max_element_vm_MPa` statistic is the maximum among element-average stresses. The weighted 95th percentile uses element volume weighting. Fixed-edge peak stress is not used as a strength or safety-factor claim.
