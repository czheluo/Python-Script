# coding=utf-8
import os
from jinja2 import Environment
__author__ = 'meng.luo'
# tool_template.jinja2 is the tool template. DO NOT CHANGE IT unless necessary.

# 定制以下变量的值，直接运行当前的脚本即可获得定制的tool，然后去修改需要完善的地方，完成tool开发。
tool_name = 'lnc_target_cis'  # 请定制
raw_tool_name = 'lnc_target_cis'
tool_description = 'lnc rna target prediction'  # 请定制

# tool_parent_dir is a directory name in /mnt/ilustre/users/sanger-dev/biocluster/src/mbio/tools/
tool_parent_dir = 'lnc_rna'  # 请定制

# called_script is expected located at: /bioinfo/rna/scripts/
# called_script is expected to be a python script which may wrap outer software written in C/java.
# we expected that all argument names are designed to be same with this tool.
called_script = 'bed2intersect.py'  # 请定制， 最好的情况是该脚本为你对外部程序的python包装

# option list. Very important
type_list = ['int', 'float', 'string', 'infile', 'outfile', ]
option_attributes = ['name', 'type', 'default', 'format', ]
option_list = [  # 请定制，该部分参数名与called_script所需参数名保持一致会减少你的工作量。
    dict(name='mrna_gtf', type=type_list[3], format="lnc_rna.gtf", ),
    dict(name='lncrna_gtf', type=type_list[3], format="lnc_rna.gtf", ),
    dict(name='lncrna_bed', type=type_list[3], format="lnc_rna.bed", ),
    dict(name='lncrna_bed', type=type_list[3], format="lnc_rna.bed", ),
    dict(name='out', type=type_list[3], format="lnc_rna.common", ),
]


# ----rendering-------do not change the following codes unless necessary---------
env = Environment()
# env.trim_blocks = True
tool_template = env.from_string(open('tool_template.jinja2').read())
result = tool_template.render(tool_name=tool_name,
                              raw_tool_name=raw_tool_name,
                              tool_parent_dir=tool_parent_dir,
                              called_script=called_script,
                              option_list=option_list,
                              tool_description=tool_description,
                              )
tools_dir = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(tools_dir, raw_tool_name+'.py'), 'w') as f:
    f.write(result)
