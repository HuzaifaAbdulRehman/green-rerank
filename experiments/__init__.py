"""Experiment drivers: sweeps, provenance, and the analyses run on their output.

Kept outside the ``green_rerank`` package on purpose. The package is a measurement
harness someone else could import; these are this project's own runs. Mixing them would
make the harness's dependency list include whatever a driver happened to need.
"""
