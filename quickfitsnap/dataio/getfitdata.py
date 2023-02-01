# Description: Class to get quantum computational database files
import warnings
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO
from zipfile import ZipFile
import gzip
import shutil
from tempfile import mkdtemp

from alive_progress import alive_bar
import ase.io

# Local scope utility functions


def ungzipfile(gzfilename, outfilename) -> None:
    """
    Uncompress gzip file format.
    Arguments:
        - gzfilename:: gzip file
        - outfilename:: output file without format spec.
    Returns:
        - None
    """
    with gzip.open(gzfilename, 'rb') as f_in:
        with open(outfilename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def retrieveCompressedVASPCalc(openurl, mpid, taskid) -> dict:
    """
    Grabs Materials Project raw VASP files from url.

    Handles:
    - Materials Project grabs from NOMAD repo.
    - JARVIS grabs from figshare
    """
    with ZipFile(BytesIO(openurl.content)) as zf:
        tmpfolder = mkdtemp(suffix='/')
        filenames = zf.namelist()
        ofiles = []  # All output files
        # Go through files and get VASP .gz
        for fname in filenames:
            if fname.endswith("gz"):
                zf.extract(fname, tmpfolder)
                gzfile = tmpfolder+fname
                ofile = gzfile.strip(".gz")
                ungzipfile(gzfile, ofile)
                ofiles.append(ofile)
            else:
                zf.extract(fname, tmpfolder)
                ofiles.append(tmpfolder+fname)

        details = {'mpid': mpid, 'taskid': taskid, 'files': ofiles}
    return details


class FitDataDetails:
    def __init__(self, urls=None,
                 meta=None,
                 codename="VASP",
                 calcoutftype="vasprun.xml",
                 reader=ase.io.read) -> None:
        self.urls = urls
        self.meta = meta
        self.codename = codename
        self.fit_datasets = None

        self.calcoutftype = calcoutftype
        self.reader = reader

    def getQECalcFiles(self, meta, dbname=None):
        NotImplementedError("'FitDataDetails' method 'getQECalcFiles'")

    def getAbinitCalcFiles(self, meta, dbname=None):
        NotImplementedError("'FitDataDetails' method 'getAbinitCalcFiles'")

    def getVASPCalcFiles(self, meta, dbname="MP"):
        """
        Grab the VASP OUTCAR and vasprun.xml files from a database calculation.

        Arguments:
            - meta:: `dict` containing keys corresponding to a material id in a database and
                     values that is a `list` of `dict` that should have keys `task_id` and `task_type`
            - dbname:: `str` the database storing the files. The default is Materials Project (MP) via NOMAD.
        Returns:
            - None
        """

        # ASSUMPTIONS: This assumes that urls and meta are paired such that when meta is
        # unravled the url entries correspond appropriately
        # TODO: Add progress bar since this can take time.

        with alive_bar(len(meta), force_tty=True, title=f"Downloading Calc. Output Files") as bar:
            iu = 0
            for matid in meta:
                for calc in meta[matid]:
                    taskid = calc['task_id']
                    u = self.urls[iu]

                    # Download
                    session = requests.Session()
                    retry = Retry(connect=5, backoff_factor=0.5)
                    adapter = HTTPAdapter(max_retries=retry)
                    session.mount('http://', adapter)
                    session.mount('https://', adapter)
                    content = session.get(u)

                    # DOESN"T DO ANYTHING
                    if dbname in ("MP", "Materials Project"):
                        details = retrieveCompressedVASPCalc(
                            content, matid, taskid)
                        self.calc_files_details.append(details)
                    if dbname in ("JARVIS", "NIST", "NIST-JARVIS"):
                        details = retrieveCompressedVASPCalc(
                            content, matid, taskid)
                        self.calc_files_details.append(details)

                    iu += 1

                time.sleep(0.02)
                bar()

    def getCalcFiles(self, meta=None, force=False):
        """
        Top level get method for calculation files
        """

        self.calc_files_details = []

        if (self.meta and meta) == None:
            ValueError("Variable 'meta' is 'None' type. Please specify.")

        if self.meta != None:
            meta = self.meta

        if self.calc_files_details:
            warnings.warn(
                "Calculation files have already been fetched; skipping! If you want to force fetch use karg `force=True`")
            if force != True:
                return None

        if self.codename == "VASP":
            self.getVASPCalcFiles(meta=meta)

    def readVASPOutFiles(self, outfile="vasprun.xml", reader=ase.io.read):
        """
        Reads in the database calculation files.

        Arguments:
            - reader::ase.io.read The atomic simulation env `read` function. See 
            https://wiki.fysik.dtu.dk/ase/ase/io/io.html#ase.io.read for more details.

        Attributes:
            - dict:: with key/value pairs begin related to meta details and values are `ase.atoms.Atoms` or `list(ase.atoms.Atoms)`
            - other if `reader` != ase.io.read
        """
        datasets = []
        for calc in self.calc_files_details:
            filetoread = next(f for f in calc['files'] if outfile in f)
            if reader == ase.io.read:
                assert filetoread.split('/')[-1] in ("OUTCAR", "vasprun.xml", "XDATCAR"), ValueError(
                    "ASE io only supports OUTCAR, vasprun.xml, or XDATCAR")
                data = reader(filetoread, index=':')
                datasets.append(data)
            else:
                NotImplementedError("Alternative 'readers'")

        # GOTCHA --> if dataset is more than one items, this will be wrong.
        self.fit_datasets = datasets  # dict(zip(self.meta.keys(),datasets))

    def readOutFiles(self):
        """
        Top level read method for calculation output files
        """

        if self.codename == "VASP":
            self.readVASPOutFiles(outfile=self.calcoutftype,
                                  reader=self.reader)
