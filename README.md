## QuickFitSNAP [WIP]

Is a python library/set of scripts that utilizes [FitSNAP](https://github.com/FitSNAP/FitSNAP) and various atomistic computational materials databases, for example [Materials Project](https://materialsproject.org/), [NIST-JARVIS](https://jarvis.nist.gov/), [QCMD](), [AFLOW](https://www.aflowlib.org/), etc., to fit quick and "dirty" interatomic potentials using SNAP formalism.

The way to use this package is as a means to quickly fit data from computational atomistic material database calculation result files. More specifically most database projects have a REST API that allows you to grab the calculation input and output files. What we are looking for is the VASP `OUTCAR` or `vasprun.xml` files that contain atomistic descriptions such as positions, forces, system energy, and cell stresses. Then we can convert these to [extended XYZ](https://github.com/libAtoms/extxyz) format or JSON using a package like [ASE](https://wiki.fysik.dtu.dk/ase/) or [PyMatgen](https://pymatgen.org/) which `FitSNAP` uses. Alternative it is possible to use the `OUTCAR` files directly using the `[SCRAPPER]` option in `FitSNAP` set to `VASP` however, this hasn't been explored yet.

<div class="alert alert-block alert-info">
<b>Warning:</b> There are no gaurantees whatsoever on the quality of the potentials fit using this approach. This is very experimental!
</div>

### Setup

You will need a python environment setup with the following:

- [FitSNAP](https://github.com/FitSNAP/FitSNAP) requirements:
        - LAMMPS as shared library with python support [LAMMPS Python](https://docs.lammps.org/Python_head.html)
        - Other [dependecies](https://github.com/FitSNAP/FitSNAP#dependencies)
- [Atomic Simulation Environment (ASE)](https://wiki.fysik.dtu.dk/ase/) 
- [PyMatgen API](https://pymatgen.org/)
- [JARVIS-tools](https://jarvis-tools.readthedocs.io/en/master/)
- [libAtoms extxyz](https://github.com/libAtoms/extxyz) to write the files rather the using ASE
- [Jupyter](https://jupyter.org/) for [example notebook](examples/ExampleOnQueryAndPrepFitSNAP.ipynb) 
- [Bayesian-Optimization](https://github.com/fmfn/BayesianOptimization) for [example notebook](examples/ExampleOnQueryAndPrepFitSNAP.ipynb)


The python package requirements for this library can be found in [requirements.txt](requirements.txt).

### Use

Since the aim of this package is to just quickly provide a "first effort" interatomic potential using the vast amount of already generated ab-initio data via open science, the objective is to just pull whatever relevant chemical system calculation details are available and fit the SNAP potential using a generic template input file. Then one can take the SNAP coefficients and parameters and assess them on predictive capability, for example, calculating the phonon disperson/DOS.

There is the aspect of hyperparameters for the fitting process that should be addressed. Mainly we need to determine how to set the weights for the different groups we specify when using FitSNAP. There are two options, 1.) we don't do anything just manual guess the weights (e.g., Ta BCC should have a high weight associated with it given its stable) or 2.) we use Bayessian optimization to find the optimal parameters given priors.


### Examples

- [AlP fit](examples/ExampleOnQueryAndPrepFitSNAP.ipynb)

