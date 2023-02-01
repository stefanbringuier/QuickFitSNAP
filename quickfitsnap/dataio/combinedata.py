# Description functions to take dataio.writefitdata Class objects
# and combine output files that match some condition in the file name
# for example if we have JARVIS and MaterialsProject for same structure and calc type.


def combineJARVISandMP(first_dataset,second_dataset,**kwargs):
    condition = kwargs["condition"]

    #if condition == 1:
    #    calc_types = ("GGA_Static","DFT-SCF")

    return None