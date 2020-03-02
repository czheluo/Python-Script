# coding=utf-8
import os
import glob
from biocluster.agent import Agent
from biocluster.tool import Tool
from biocluster.core.exceptions import OptionError
import unittest
# import pandas as pd
__author__ = 'MENGLUO'


class lnc_target_cisAgent(Agent):
    """
    lnc rna target prediction
    """
    def __init__(self, parent):
        super(lnc_target_cisAgent, self).__init__(parent)
        options = [
            {'type': 'infile', 'name': 'mrna_gtf', 'format': 'lnc_rna.gtf'},
            {'type': 'infile', 'name': 'lncrna_gtf', 'format': 'lnc_rna.gtf'},
            {'type': 'infile', 'name': 'lncrna_bed', 'format': 'lnc_rna.bed'},
            {'type': 'infile', 'name': 'lncrna_bed', 'format': 'lnc_rna.bed'},
            {'type': 'infile', 'name': 'out', 'format': 'lnc_rna.common'},
        ]
        self.add_option(options)

    def check_options(self):
        pass

    def set_resource(self):
        self._cpu = 1
        self._memory = "{}G".format('?')

    def end(self):
        result_dir = self.add_upload_dir(self.output_dir)
        result_dir.add_relpath_rules([
            [".", "", ""]
            ])
        """
        # more detail
        result_dir.add_regexp_rules([
            [r"*.xls", "xls", "xxx"],
            [r"*.list", "", "xxx"],
            ])
        """
        super(lnc_target_cisAgent, self).end()


class lnc_target_cisTool(Tool):
    """
    lnc rna target prediction
    """
    def __init__(self, config):
        super(lnc_target_cisTool, self).__init__(config)
        software_dir = self.config.SOFTWARE_DIR
        self.python_path = 'program/Python/bin/python'
        self.bed2intersect.py = software_dir + '/bioinfo/rna/scripts/bed2intersect.py.py'
        self.gcc = software_dir + '/gcc/5.1.0/bin'
        self.gcc_lib = software_dir + '/gcc/5.1.0/lib64'
        self.set_environ(PATH=self.gcc, LD_LIBRARY_PATH=self.gcc_lib)
        self.r_path = software_dir + "/program/R-3.3.1/bin:$PATH"
        self._r_home = software_dir + "/program/R-3.3.1/lib64/R/"
        self._LD_LIBRARY_PATH = software_dir + "/program/R-3.3.1/lib64/R/lib:$LD_LIBRARY_PATH"
        self.set_environ(PATH=self.r_path, R_HOME=self._r_home, LD_LIBRARY_PATH=self._LD_LIBRARY_PATH)

    def run_bed2intersect.py(self):
        cmd = '{} {} '.format(self.python_path, self.bed2intersect.py)
        cmd += '-{} {} '.format("mrna_gtf", self.option("mrna_gtf").prop['path'])
        cmd += '-{} {} '.format("lncrna_gtf", self.option("lncrna_gtf").prop['path'])
        cmd += '-{} {} '.format("lncrna_bed", self.option("lncrna_bed").prop['path'])
        cmd += '-{} {} '.format("lncrna_bed", self.option("lncrna_bed").prop['path'])
        cmd += '-{} {} '.format("out", self.option("out").prop['path'])
        cmd_name = 'lnc_target_cis'
        command = self.add_command(cmd_name, cmd)
        command.run()
        self.wait()
        if command.return_code == 0:
            self.logger.info("{} Finished successfully".format(cmd_name))
        elif command.return_code is None:
            self.logger.warn("{} Failed and returned None, we will try it again.".format(cmd_name))
            command.rerun()
            self.wait()
            if command.return_code is 0:
                self.logger.info("{} Finished successfully".format(cmd_name))
            else:
                self.set_error("{} Failed. >>>{}".format(cmd_name, cmd))
        else:
            self.set_error("{} Failed. >>>{}".format(cmd_name, cmd))

    def set_output(self):
        pass
        '''Example:
        diff_files = glob.glob(self.option("output") + '/*_vs_*.xls')
        diff_list = glob.glob(self.option("output") + '/*.DE.list')
        diff_summary = glob.glob(self.option("output") + '/*summary.xls')
        all_files = diff_files + diff_list + diff_summary
        for each in all_files:
            fname = os.path.basename(each)
            link = os.path.join(self.output_dir, fname)
            if os.path.exists(link):
                os.remove(link)
            os.link(each, link)
        '''

    def run(self):
        super(lnc_target_cisTool, self).run()
        self.run_bed2intersect.py()
        self.set_output()
        self.end()


class TestFunction(unittest.TestCase):
    """
    This is test for the tool. Just run this script to do test.
    """
    def test(self):
        import random
        from mbio.workflows.single import SingleWorkflow
        from biocluster.wsheet import Sheet
        test_dir='/mnt/ilustre/users/sanger-dev/biocluster/src/mbio/tools/lnc_rna/test_files'
        data = {
            "id": "lnc_target_cis" + str(random.randint(1, 10000)),
            "type": "tool",
            "name": "lnc_rna.lnc_target_cis",
            "instant": False,
            "options": dict(
                mrna_gtf=test_dir + "/" + "? infile name",
                lncrna_gtf=test_dir + "/" + "? infile name",
                lncrna_bed=test_dir + "/" + "? infile name",
                lncrna_bed=test_dir + "/" + "? infile name",
                out=test_dir + "/" + "? infile name",
            )
           }
        wsheet = Sheet(data=data)
        wf = SingleWorkflow(wsheet)
        wf.run()


if __name__ == '__main__':
    unittest.main()
