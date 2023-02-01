# Description: Class to write folder and file structure for FitSNAP
import os, shutil
import time
import json

from .getfitdata import FitDataDetails

from alive_progress import alive_bar
from ase.io import write
from extxyz import write as writexyz


class GetAndWriteFitData(FitDataDetails):
    def __init__(self,fetchread=True,
                      folderpath="./XYZ",
                      outfrmt="extxyz",
                      overwrite=True,
                      **kwargs) -> None:
        super().__init__(**kwargs)
        
        if fetchread:
            self.getCalcFiles()
            self.readOutFiles()

        self.folderpath=folderpath
        
        # Remove and make temp data folder
        if overwrite:
            try:
                shutil.rmtree(self.folderpath)
            except:
                pass
        
        os.makedirs(self.folderpath)


        self.outfrmt=outfrmt

    @staticmethod
    def writeASEAtomsToFile(atoms,pathandname,suffix=".xyz",frmt="extxyz"):
        """
        write a file to a fully resolved path in format supported by ase
        
        !!!  Note
             The method should be exposed to `FitDataDetails` objects 
        """
        write(pathandname+suffix,atoms,format=frmt)


    @staticmethod
    def writeJSON(atoms, jsonbase,codename="VASP"):
        """
        This function code is part of and modified from FitSNAP:

            https://github.com/FitSNAP/FitSNAP/blob/master/tools/VASPxml2JSON.py

        Distributed/Redistributed under the license:
        
            https://github.com/FitSNAP/FitSNAP/blob/master/LICENSE
       
        Arguments:
            - atoms:: ASE Atoms object - data to write
            - jsonbase:: str - folder name/base for each configuration
        """
        if os.path.exists(jsonbase):
            shutil.rmtree(jsonbase)
        os.makedirs(jsonbase)
        
        if type(atoms) is not list:
            configs = [atoms]
        else:
            configs = atoms

        for i,config in enumerate(configs):
            data = {}
            data["Positions"] = config.positions.tolist()
            data["Forces"] = config.get_forces().tolist()
            data["Stress"] = config.get_stress(voigt=False).tolist()
            data["Lattice"] = config.cell.tolist()
            data["Energy"] = config.get_total_energy()
            data["NumAtoms"] = config.get_global_number_of_atoms()
            data["AtomTypes"] = config.get_chemical_symbols()
            #data["computation_code"] = codename


            jsonfile = open(jsonbase+"/"+str(i+1)+".json", "w")
       
            allData = [data]
            allDataHeader = {}
            allDataHeader["EnergyStyle"] = "electronvolt"
            allDataHeader["StressStyle"] = "bar"
            allDataHeader["AtomTypeStyle"] = "chemicalsymbol"
            allDataHeader["PositionsStyle"] = "angstrom"
            allDataHeader["ForcesStyle"] = "electronvoltperangstrom"
            allDataHeader["LatticeStyle"] = "angstrom"
            allDataHeader["Data"] = allData

            myDataset = {}

            myDataset["Dataset"] = allDataHeader
            json.dump(myDataset, jsonfile, indent=2, sort_keys=True)  #if you want the expanded, multi-line format
            jsonfile.close()
        return


    def writefitfiles(self):
        """
        Uses write output files.
        """
        i = 0
        self.outfilelist = []
        
        with alive_bar(len(self.meta), force_tty=True, title=f"Write XYZ Fit Dataset Files") as bar:
            for datasetname in self.meta:
                for calc in self.meta[datasetname]:
                    taskid = calc['task_id']
                    tasktype = calc['task_type'].replace(' ','_')
                    atoms = self.fit_datasets[i]
                    chemsys = atoms[0].get_chemical_formula() # Possible GOTCHA: Assumes chemical formula is same for all images
                    outname = self.folderpath+"/"+ \
                            chemsys + '_' + datasetname + \
                            '_' + taskid + '_' + tasktype

                    if self.outfrmt == 'extxyz':
                        self.writeASEAtomsToFile(atoms,outname)
                    if self.outfrmt == 'json':
                        self.writeJSON(atoms,outname,codename=self.codename)

                    self.outfilelist.append(outname)
                    i += 1
                
                time.sleep(0.02)
                bar()




    

