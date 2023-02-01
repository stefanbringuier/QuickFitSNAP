from itertools import combinations_with_replacement as combinations

SNAP_IN_TEMPLATE= """
[BISPECTRUM]
numTypes = %i
twojmax = %s
rcutfac = 4.67637
rfac0 = 0.99363
rmin0 = 0.0
wj = %s
radelem = %s
type = %s
wselfallflag = 0
chemflag = 0
bzeroflag = 0
quadraticflag = 0

[CALCULATOR]
calculator = LAMMPSSNAP
energy = 1
force = 1
stress = 1

[ESHIFT]
%s

[SOLVER]
solver = SVD
compute_testerrs = 1
detailed_errors = 1

[SCRAPER]
scraper = %s

[PATH]
dataPath = %s

[OUTFILE]
metrics = %s
potential = %s

[REFERENCE]
units = metal
atom_style = atomic
pair_style = hybrid/overlay zero 10.0 zbl 4.0 4.8
pair_coeff1 = * * zero
%s

[GROUPS]
# name size eweight fweight vweight
group_sections = name training_size testing_size eweight fweight vweight
group_types = str float float float float float
smartweights = 0 
random_sampling = 0
%s

[EXTRAS]
dump_descriptors = 1
dump_truth = 1
dump_weights = 1
dump_dataframe = 1

[MEMORY]
override = 0
""" 

def genericTemplate(template='SNAP',
                    numtypes=1,
                    twojmax=[6],
                    wj =[1.0],
                    radelem=[0.5],
                    species=['Ta'],
                    eshift=[0.0],
                    scraper='XYZ',
                    datapath='XYZ',
                    masses=[[73,73]],
                    metricfile="results.md",
                    potfitname="Ta_potential"):
    """
    Generate a generic SNAP input file string. 
    """
    
    typenames = " ".join(species)
    eshift = "\n".join(["%s = %f" %(e[0],e[1]) for e in zip(species,eshift)])
    pairs = list(combinations(range(1,numtypes+1),2))
    typemasses = ""
    for i,m in enumerate(masses):
        prefix = "pair_coeff%i = %i %i zbl " %(i+2,*pairs[i])
        typemasses += prefix + " ".join(map(str,m)) + "\n"

    inject = (numtypes,
              " ".join(map(str,twojmax)),
              " ".join(map(str,wj)),
              " ".join(map(str,radelem)),
              " ".join(species),
              eshift,
              scraper,
              datapath,
              metricfile,
              potfitname,
              typemasses)

    if template == 'SNAP':
        return SNAP_IN_TEMPLATE %(*inject,'%s')
    elif template == 'ACE':
        return NotImplementedError("ACE features not implemented")
    else:
        return 0

