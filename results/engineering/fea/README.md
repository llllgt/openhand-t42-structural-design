# Revision B raw finite-element results

`raw-revB.zip` contains the six compressed NumPy arrays referenced by the JSON records.
SHA-256 hashes are in `raw_checksums.json`. Units: mm, N, MPa.

- `points`, `tets`, `triangles`: linear geometric mesh and boundary facets.
- `displacement`: displacement at original mesh vertices only. JSON additionally reports the maximum over all quadratic element displacement nodes, including edge midpoints; it is still a sampled maximum.
- `element_vm`, `element_principal`: element-integrated averages, not converged local stress peaks.
- `central_region`: element-center region |X|<13, |Y|<29 used for the local diagnostic.

The applied resultant includes a factor 1.5. E=1650 MPa, nu=0.35; forces are distributed on the four reference seats. This is not a solved full assembly contact model. Foundation stiffness values 100 and 10 N/mm3 are sensitivity assumptions, not measured joint stiffnesses.
