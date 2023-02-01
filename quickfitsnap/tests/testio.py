import unittest
import os, shutil
from dataio import FitDataDetails, GetAndWriteFitData


class TestFitDataDetails(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestFitDataDetails, self).__init__(*args, **kwargs)

        self.urls = ['https://nomad-lab.eu/prod/rae/api/raw/query?file_pattern=vasprun*&file_pattern=OUTCAR*&external_id=mp-1400968',
                     'https://nomad-lab.eu/prod/rae/api/raw/query?file_pattern=vasprun*&file_pattern=OUTCAR*&external_id=mp-1437884']
        self.meta_data = {'mp-1001602': [{'task_id': 'mp-1400968', 'task_type': 'GGA Static'}],
                          'mp-1008487': [{'task_id': 'mp-1437884', 'task_type': 'GGA Static'}]}

    def test_getVASPCalcFiles(self):
        fitdatadetails = FitDataDetails(self.urls,
                                        meta=self.meta_data,
                                        codename='VASP')

        fitdatadetails.getCalcFiles()
        self.assertIsNotNone(fitdatadetails.calc_files_details,
                             msg="Failed get VASP calculation files.")

    def test_readVASPOutFiles(self):
        fitdatadetails = FitDataDetails(self.urls,
                                        meta=self.meta_data,
                                        codename='VASP')

        fitdatadetails.getCalcFiles()
        fitdatadetails.readVASPOutFiles()

        self.assertIsNotNone(fitdatadetails.fit_datasets,
                             msg="Failed to read VASP calculation files.")


class TestWriteAndGetFitData(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestWriteAndGetFitData, self).__init__(*args, **kwargs)

        self.urls = ['https://nomad-lab.eu/prod/rae/api/raw/query?file_pattern=vasprun*&file_pattern=OUTCAR*&external_id=mp-1400968',
                     'https://nomad-lab.eu/prod/rae/api/raw/query?file_pattern=vasprun*&file_pattern=OUTCAR*&external_id=mp-1437884']
        self.meta_data = {'mp-1001602': [{'task_id': 'mp-1400968', 'task_type': 'GGA Static'}],
                          'mp-1008487': [{'task_id': 'mp-1437884', 'task_type': 'GGA Static'}]}
    
    def test_writeASEXYZext(self):
        prepdata = GetAndWriteFitData(urls=self.urls,
                                      meta=self.meta_data,
                                      folderpath="/tmp/XYZ_test")
        
        # Remove and make temp data folder
        #if os.path.exists(prepdata.folderpath):
        #    shutil.rmtree(prepdata.folderpath)
        #os.makedirs(prepdata.folderpath)

        prepdata.writeASEXYZext()

        self.assertIsNotNone(os.listdir(prepdata.folderpath))


if __name__ == '__main__':
    unittest.main()
