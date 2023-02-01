# Description: Class to query MaterialsProject.org
# Notes: The query class methods don't cache any information about already downloaded files.

import warnings
import re

from pymatgen.ext.matproj import TaskType
from pymatgen.ext.matproj import MPRester as MPResterLegacy


class MaterialsProjectQuery:
    def __init__(self, api_key,
                 chemsys,
                 task_types=None,
                 file_patterns=None,
                 unary=True,
                 legacympr=True,
                 defaults=True) -> None:
        self.api_key = api_key
        self.chemicalsystem = chemsys
        self.legacy = legacympr
        if self.legacy:
            self.MPRester = MPResterLegacy

        if defaults:
            self.setDefaultTaskTypes()
            self.setDefaultFilePatterns()
        else:
            self.task_types = task_types
            self.file_patterns = file_patterns

        self.queryMPChemSys(unary)



    def queryMPChemSys(self, unary):
        with self.MPRester(self.api_key) as mpr:
            chemicalsystem = self.chemicalsystem.split("-")
            materials = mpr.query(criteria={"elements": {"$all": chemicalsystem},
                                            "nelements": {"$lte": len(chemicalsystem)}},
                                  properties=["pretty_formula", "material_id"])
            if unary:
                for s in chemicalsystem:
                    unaries = mpr.query(criteria={"elements": s,
                                                  "nelements": 1},
                                        properties=["pretty_formula", "material_id"])
                    materials.extend(unaries)
            
        self.found_materials = materials

    def legacyAssert(self):
        assert self.legacy, ValueError(
            "Method only supported for legacy MPRester.")

    def setDefaultTaskTypes(self):
        self.legacyAssert()
        mptasktypes = (TaskType.GGA_STATIC,
                       TaskType.GGA_OPT,
                       TaskType.GGA_LINE,
                       TaskType.GGAU_DEF,
                       TaskType.GGAU_OPT,
                       TaskType.GGA_DEF,
                       TaskType.SCAN_OPT)

        self.task_types = list(mptasktypes)

    def setDefaultFilePatterns(self):
        self.legacyAssert()
        mpfilepat = ("vasprun*", "OUTCAR*", "XDATCAR*")
        self.file_patterns = list(mpfilepat)

    def getMPCalcOutFileInfo(self, mpids=None):
        """
        Get meta data and urls for VASP calculation outputs for Materials Project entry.

        Arguments:
            - mpids:: list of materials project entry ids
        Returns:
            - dict:: of materials project ids keys with list of dict of task_ids and task_type
            - list:: urls corresponding to calculation outputs for mpid, task_id, and task_type
        """
        self.legacyAssert()

        if not mpids:
            mpids = [entry['material_id'] for entry in self.found_materials]
            assert mpids, ValueError("Class attribute `found_materials` not set. Please call `queryMPChemSys` method.")
       
        with self.MPRester(self.api_key) as mpr:
            # KNOWN ISSUE: If the files don't exist on NOMAD etc, the meta_data is still
            # returned but not the urls and therefor will cause a issue in intface.py classes
            # TODO: Find a solution to try/catch and then pop out failed attemp from meta_data
            # APPROACH: catch UserWarning from MPRester and parse the message to remove problem entry
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                meta_data, urls = mpr.get_download_info(mpids,
                                                        task_types=self.task_types,
                                                        file_patterns=self.file_patterns)
            
            if len(w) == 1 and issubclass(w[-1].category, UserWarning):
                msg = str(w[-1].message)
                print(msg)
                print("Removing entries with no urls from meta data!.")
                mpidtaskpttrn = re.compile(r'mp\-\d*')
                prblmtaskids = mpidtaskpttrn.findall(msg)
                delk = []
                for k in meta_data:
                    for i in meta_data[k]:
                        if i['task_id'] == prblmtaskids:
                            delk.append(k)
                for dk in delk:
                    del meta_data[dk]


        return meta_data, urls

