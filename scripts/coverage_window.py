# -*- coding: utf-8 -*-
# __author__ = 'meng.luo'
# modified 2018.09.04

from biocluster.agent import Agent
from biocluster.tool import Tool
from biocluster.core.exceptions import OptionError
import os
import datetime

starttime = datetime.datetime.now()
class CoverageWindowAgent(Agent):
    """
    软件: depth_stat_window，处理samtools depth的数据，做覆盖度图
    """
    def __init__(self, parent):
        super(CoverageWindowAgent, self).__init__(parent)
        options = [
            {"name": "depth_file", "type": "infile", "format": "dna_evolution.depth"},  # samtools的depth方法的结果文件
            {"name": "step_num", "type": "int", "default": 200}
        ]
        self.add_option(options)

    def check_options(self):
        if not self.option("depth_file"):
            raise OptionError("请设置depth_file路径", code="34902601")
        if not self.option("step_num") in [5, 10, 50, 100, 200, 500]:
            raise OptionError("step_num 只能是5K，10K，50K,100K，200K，500K", code="34902602")

    def set_resource(self):
        self._cpu = 2
        self._memory = "5G"

    def end(self):
        super(CoverageWindowAgent, self).end()


class CoverageWindowTool(Tool):
    def __init__(self, config):
        super(CoverageWindowTool, self).__init__(config)
        self.depth_stat_window = "bioinfo/WGS/depth_stat_windows"
    def run_depth_stat_window(self):
        """
        depth_stat_window
        """
        sample_name = os.path.basename(self.option("depth_file").prop["path"]).split(".")[0]
        depth_fordraw = sample_name + ".coverage.xls"
        cmd = "{} -i {} -o {} -w {}".format(self.depth_stat_window, self.option("depth_file").prop["path"],
                                            self.work_dir + "/" + depth_fordraw, self.option("step_num")*1000)
        # cmd = "{} -i {} -o {} -w {}".format(self.depth_stat_window, self.option("depth_file").prop["path"],
        #                                     self.output_dir + "/" + depth_fordraw, self.option("step_num") * 1000)
        command = self.add_command("depth_stat_window", cmd).run()
        self.wait()
        if command.return_code == 0:
            self.logger.info("depth_stat_window运行完成")
        else:
            self.set_error("depth_stat_window运行失败", code="34902601")
        if os.path.exists(self.output_dir + "/" + depth_fordraw):
            os.remove(self.output_dir + "/" + depth_fordraw)
        os.link(self.work_dir + "/" + depth_fordraw, self.output_dir + "/" + depth_fordraw)

    def run(self):
        super(CoverageWindowTool, self).run()
        self.run_depth_stat_window()
        self.end()
