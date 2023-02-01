# Description: Class to setup and perform a fit using FitSNAP
import os
from shutil import copyfile
from tempfile import mkstemp
from mpi4py import MPI
import numpy as np


from .templates import genericTemplate

# WARNING!!! NEED TO MANUAL UPDATE THIS BASED ON FILES AVAILABLE FROM
# MaterialProject, JARVIS, etc.
SUPPORTED_CALC_TYPES = ('DFT-SCF',
                        'GGA_Static',
                        'FD_ELAST')

class SetupAndPerformFit():
    def __init__(self,folderpath,
                      training_names,
                      copy_file=True,
                      assignbycalctype=False,
                      **kwargs):
        """
        Arguments
            - training_names:: list - Is a list of the path+filenames for training data
        """
        self.folderpath = folderpath
        self.training_names = training_names
        self.assignbycalctype = assignbycalctype
        self.genInputTemplate(datapath=self.folderpath,**kwargs)
        if copy_file:
            destf = os.getcwd()+'/'+self.inputfilename.split('/')[-1]
            copyfile(self.inputfilename,destf)


    def genWeights(self,normdist=False):
        if not normdist:
            weights ="1.0 0.0 1.0 0.1 1.0e-12"
        else:
            NotImplementedError("Normal distribution of weights")
        
        groups =""""""
        for n in self.training_names:
            groups = groups + "%s = %s\n" %(n,weights)

        return groups

    def genInputTemplate(self,**kwargs):
        """
        For kwargs see templates.py
        """
        training_names_weights = self.genWeights()
        tmpinput = genericTemplate(**kwargs) %(training_names_weights)
        tmpinputfile = mkstemp(suffix=".in")[1]
        with open(tmpinputfile,'w') as tf:
            tf.write(tmpinput)
        self.inputfilecontent = tmpinput
        self.inputfilename = tmpinputfile

    def changeWeights(self,**kwargs):
        """
        Code adapted from:
            https://github.com/FitSNAP/FitSNAP/blob/master/examples/library/loop_over_fits/example.py

        Distributed/redistributed under license:
            https://github.com/FitSNAP/FitSNAP/blob/master/LICENSE

        IMPORTANT:
        the kwargs should have the following format:
            {'GROUPNAME_parameter':value} 

            example: {'Ta_mp-50_mp-1440654_GGA_STATIC_eweight': 100.0}

        TO PONDER: 
        The primary purpose of this method is for use during Bayesian Opt, but we allow 
        for changing all the weights of each GROUP individually. This maybe a bad idea, given
        we want to probably weight ground-state GGA calculations the same and finite-difference
        for elastic constant calculations the same, not allow for variability. Essentially we want to
        find the weights for the different types of calculations not individiual groups.

        The way to do this is then to parse the string name of the GROUP and match. This way the the kwargs
        passed would just be something like {'SCF-GGA_eweight': 100.0, 'FD-ELAST_eweight': 1.0 ....}
        """

        # Change the weights on group first
        for kkey in self.config.sections['GROUPS'].group_table:
            key = kkey
            if self.assignbycalctype:
                for c in SUPPORTED_CALC_TYPES:
                    if c in kkey:
                        key = c           

            for subkey in self.config.sections['GROUPS'].group_table[kkey]:
                if ("weight" in subkey):
                    # change the weight
                    weight_value = kwargs[key+'_'+subkey]
                    self.config.sections['GROUPS'].group_table[kkey][subkey] = weight_value

        # Now change weights on configurations in group
        # Note this is done by reference
        for i, configuration in enumerate(self.snap.data):
            group_name = configuration['Group']
            new_weight = self.config.sections['GROUPS'].group_table[group_name]
            for key in self.config.sections['GROUPS'].group_table[group_name]:
                if ("weight" in key):
                    # set new weight 
                    configuration[key] = new_weight[key]
        
        return None

        
    
    def changeBispectrum(self,**kwargs):
        """
        Code adapted from:
            https://github.com/FitSNAP/FitSNAP/blob/master/examples/library/loop_over_fits/example.py

        Distributed/redistributed under license:
            https://github.com/FitSNAP/FitSNAP/blob/master/LICENSE

        IMPORTANT:
        the kwargs should have the following format:
        """

        bkeys = ('twojmax','wj','radelem')
        bparams = {}
        for b in bkeys:
            values = []
            for k in kwargs:
                if k.startswith(b):
                    # ISSUE: bayes_opt can't handle discrete param values so we have to
                    # manual abuse.
                    if k.startswith('twojmax'):
                        v = str(int(float(kwargs[k])))
                    else:
                        v = str(kwargs[k])
                    values.append(v)
            bparams[b] = values

        self.config.sections['BISPECTRUM'].twojmax = bparams['twojmax']
        self.config.sections['BISPECTRUM'].wj = bparams['wj']
        self.config.sections['BISPECTRUM'].radelem = bparams['radelem']
        # These parameters are just single values so doesn't matter
        self.config.sections['BISPECTRUM'].rcutfac = kwargs['rcutfac']
        self.config.sections['BISPECTRUM'].rfac0 = kwargs['rfac0']
        self.config.sections['BISPECTRUM']._generate_b_list()

    def clearFitSNAP(self):
        del self.pt
        del self.config
        del self.snap
        
    def runFitSNAP(self,**kwargs):
        """
        This is a blackbox function with regard to bayes_opt. kwargs must
        match use in methods changehyper and changeWeights.

        The optimization is on mean-absolute error on the forces of the training data.

        NOTE: FitSNAP has a very specific module use and class instantiation sequence and seems
        that if not followed issues with shared arrays via ParallelTools arise.
        """
        #comm = MPI.COMM_WORLD
        from fitsnap3lib.tools.dataframe_tools import DataframeTools
        from fitsnap3lib.parallel_tools import ParallelTools
        self.pt= ParallelTools()
        from fitsnap3lib.io.input import Config
        self.config = Config(arguments_lst=[self.inputfilename,"--overwrite"])
        from fitsnap3lib.fitsnap import FitSnap
        self.snap = FitSnap()
        from fitsnap3lib.io.output import output
        from fitsnap3lib.initialize import initialize_fitsnap_run

        self.pt.create_shared_bool = False
        self.pt.check_fitsnap_exist = False

        self.snap.delete_data = True
        self.snap.scraper.scrape_groups()
        self.snap.scraper.divvy_up_configs()
        self.snap.data = self.snap.scraper.scrape_configs()
        
        if kwargs:
            self.changeBispectrum(**kwargs)
            self.changeWeights(**kwargs)

        self.snap.calculator.shared_index=0
        self.snap.calculator.distributed_index=0 
        self.snap.process_configs()
        self.pt.all_barrier()


        self.snap.solver.perform_fit()
        self.snap.solver.fit_gather()

        self.snap.solver.errors = []
        self.snap.solver.error_analysis()

        self.snap.write_output()

        df_tool = DataframeTools(self.snap.solver.df)
        mae_energy = df_tool.calc_error("Energy","Training")
        mae_force = df_tool.calc_error("Force", "Training")
        # TODO: Check if these are unweighted or weighted. Need to grab the mae on stress ourself
        sdf = self.snap.solver.df[self.snap.solver.df['Row_Type'] == 'Stress']
        mae_stress = np.sum(np.abs(sdf['truths']-sdf['preds']))/ len(sdf.index)

        del self.snap
        del self.config
        del self.pt

        comp_mae = -1.0e0*np.log(mae_energy) + \
             -1.0e0*np.log(mae_force) + \
             -1.0e0*np.log(mae_stress)
        return comp_mae






