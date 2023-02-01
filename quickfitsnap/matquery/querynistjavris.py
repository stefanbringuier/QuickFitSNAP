# Description: Class to query the NIST-Jarvis Database.
# Notes: The query class methods don't cache any information about already downloaded files.
import pandas as pd

from jarvis.db.figshare import get_db_info, data, get_request_data, get_jid_data


class JARVISQuery:
    def __init__(self,
                 chemsys,
                 databasename=None,
                 task_types=None,
                 file_patterns=None,
                 dbload_pandasfrmt=True,
                 unary=True,
                 defaults=True) -> None:

        self.chemicalsystem = chemsys

        if defaults:
            self.setDefaultDatabase()
            self.setDefaultTaskTypes()
            self.setDefaultFilePatterns()
        else:
            self.databasename = databasename
            self.task_types = task_types
            self.file_patterns = file_patterns

        self.dbload_pandasfrmt = dbload_pandasfrmt
        self.unary = unary

        self.loadAndQuery()

    def getJARVISDatabaseNames(self):
        return list(get_db_info().keys())

    def setDefaultDatabase(self):
        self.databasename = 'dft_3d'

    def setDefaultTaskTypes(self):
        jarvistasktypes = ("FD-ELAST",
                           "DFT-SCF")

        self.task_types = list(jarvistasktypes)

    def setDefaultFilePatterns(self):
        jarvisfilepat = ("vasprun*", "OUTCAR", "XDATCAR")
        self.file_patterns = list(jarvisfilepat)

    def loadDatabase(self, pandasfrmt=True):
        db = data(self.databasename)
        if pandasfrmt:
            self.database = pd.DataFrame(db)
        else:
            self.database = db

    def queryDatabase(self, unary=True, pandasfrmt=True):
        chemicalsystem = sorted(self.chemicalsystem.split("-"))
        searchfrmt = "-"+"-".join(chemicalsystem)
        if pandasfrmt:
            mask = self.database["search"] == searchfrmt
            self.found_materials = self.database[mask]
            if unary:
                for s in chemicalsystem:
                    unaryfrmt = "-"+"".join(s)
                    mask = self.database["search"] == unaryfrmt
                    combined = pd.concat(
                        [self.found_materials, self.database[mask]])
                    self.found_materials = combined
        else:
            NotImplementedError(
                "Other JARVIS database fomart queries. Please use pandas")

    def loadAndQuery(self):
        self.loadDatabase(pandasfrmt=self.dbload_pandasfrmt)
        self.queryDatabase(unary=self.unary, pandasfrmt=self.dbload_pandasfrmt)

    def getJARVISCalcOutFileInfo(self, jarvisdb=None):
        """
        Get meta data and urls for VASP calculation outputs from JARVIS database in a pandas dataframe representation.

        Arguments:
            - jarvisids:: a pandas dataframe which has column names 'jid' and 'raw_files'
        Returns:
            - dict:: of materials project ids keys with list of dict of task_ids and task_type
            - list:: urls corresponding to calculation outputs for mpid, task_id, and task_type
        """

        if jarvisdb:
            found_materials = jarvisdb
            assert not found_materials.empty, ValueError(
                "Provided pandas database has incorrect column names or is empty.")
        else:
            found_materials = self.found_materials
            assert not found_materials.empty, ValueError(
                "Class attribute `found_materials` not set or empty. Please call `queryDatabase` method.")

        # Format meta_data in Materials Project  style
        # {"mp_id":["task_id": str, "task_type": str]}
        # Creates meta data and file list in the style of Materials project `get_download_info` MPRester method call
        # length of urls sould be same as flatten meta_dataa
        urls = []
        meta_data = {}
        for i, j in enumerate(found_materials['jid']):
            raw_files_info = found_materials.iloc[i]['raw_files']
            ref_id = found_materials.iloc[i]['reference']
            meta_data[j] = []
            for info in raw_files_info:
                task, _, url = info.split(',')
                if task in self.task_types:
                    meta_data[j].append({'task_id': ref_id, 'task_type': task})
                    urls.append(url)
            #Remove entry if no task_types found        
            if not meta_data[j]:
                del meta_data[j]

        return meta_data, urls
