# coding=utf-8
from __future__ import print_function
import sys
import os
from collections import defaultdict

"""
usage: python qc.py heshan_MJ201605231016 /mnt/ilustre/users/deqing.gu/project/
1. 对于有多个下机路径的样本，可以另起一行填写信息。
2. 对于有多个下机路径的样本，也可以在一行当中写完所有信息，但要求lane_id和data_path的信息一一对应，且用“；”分隔。如下：
lane_id project_id  sample_id   new_name    data_path
0715lane5;0726lane6 xxx_mjxxx   name    newname /mnt/xxx/20160715hiseq4000;/mnt/xxx/20160715hiseq4000;
###########################################################################################
"heshan_MJ201605231016.info" should be formated like this, 'tab' as separator:
lane_id project_id  sample_id   new_name    data_path   ----> this headline is required
0715lane5   heshan_MJ201605231016   1   1-A /mnt/ilustre/data-split/hiseq/hiseq4000/20160715hiseq4000
0715lane5   heshan_MJ201605231016   2   1-B /mnt/ilustre/data-split/hiseq/hiseq4000/20160715hiseq4000
0715lane5   heshan_MJ201605231016   3   2-A /mnt/ilustre/data-split/hiseq/hiseq4000/20160715hiseq4000
0715lane5   heshan_MJ201605231016   4   2-B /mnt/ilustre/data-split/hiseq/hiseq4000/20160715hiseq4000
############################################################################################
"""

info = sys.argv[1]
work_path = sys.argv[2]


def find_sample_paths(lane_id, sample_id):
    def shell_find(path, pattern):
        tmp = os.popen('find {} -name "{}"'.format(path, pattern))
        return tmp

    def find_modes(lane, sample):
        # searching order is important
        paths = list()
        paths.append(shell_find(each_path, sample+'_*L00'+lane[-1]+'*001.fastq.gz'))
        paths.append(shell_find(each_path, '*'+lane+'-'+sample+'*_*R?.fastq.gz'))
        paths.append(shell_find(each_path, '*'+lane+'*-'+sample+'_*R?.fastq.gz'))
        paths.append(shell_find(each_path, '*'+lane+'*'+sample+'*_R?.fastq.gz'))
        paths.append(shell_find(each_path, '*'+lane+'*'+sample+'*_R*00?.fastq.gz'))
        paths.append(shell_find(each_path, sample+'_*'+'.fq.gz'))
        paths.append(shell_find(each_path, sample+'_*'+'.fastq.gz'))
        paths.append(shell_find(each_path, '*'+lane[-5:]+'*'+sample+'_*'+'.fq.gz'))

        return paths
    all_paths = find_modes(lane_id, sample_id)
    if "_" in sample_id:
        tmp_id = sample_id.replace('_', '-')
        all_paths_2 = find_modes(lane_id, tmp_id)
        return all_paths + all_paths_2
    else:
        return all_paths

# parse information in info
with open(info, 'r') as f:
    head_line = f.readline()
    head_list = head_line.lower().strip().split('\t')
    lane_ind = head_list.index('lane_id')
    project_ind = head_list.index('project_id')
    sample_ind = head_list.index('sample_id')
    new_name_ind = head_list.index('new_name')
    path_ind = head_list.index('data_path')

    all_info = defaultdict(dict)
    for line in f:
        if len(line.strip()) <= 1:
            continue
        tmp_list = line.strip().split('\t')
        # print(tmp_list)
        project_id = tmp_list[project_ind]
        lane_ids = tmp_list[lane_ind].split(";")
        sample_id = tmp_list[sample_ind]
        new_name = tmp_list[new_name_ind]
        path_ids = tmp_list[path_ind].split(";")
        # all_info -- {project_id:{sample_id:(lane_id, [abs_paths])}
        abs_paths = []
        abs_paths_lanes = []  # store each lane id of abs_path
        for lane_id, each_path in zip(lane_ids, path_ids):
            print('searching in', each_path)
            if lane_id:
                lane_id = lane_id.strip()
            else:
                break
            if each_path:
                each_path = each_path.strip()
            else:
                break
            # we try to find the sample in the following ways, in order!
            all_paths = find_sample_paths(lane_id, sample_id)
            find_results = []
            for i in all_paths:
                for ps_line in i:
                    if ps_line:
                        find_results.append(ps_line.strip())
                        abs_paths.append(ps_line.strip())
                        abs_paths_lanes.append(lane_id)
                        print('--Find->', ps_line.strip())
                if find_results:
                    #print(all_paths,i)
                    # if found the sample, other finding results will be ignored
                    break
            if not find_results:
                print(sample_id, "was not found in", each_path)
                print('Maybe the sample name is wrong, or you may add more searching mode')

        if sample_id not in all_info[project_id]:
            all_info[project_id][sample_id] = (abs_paths_lanes, abs_paths, new_name)
        else:
            for each in abs_paths_lanes:
                all_info[project_id][sample_id][0].append(each)
            for each in abs_paths:
                all_info[project_id][sample_id][1].append(each)
# print(all_info)

# create links for raw data
for project in all_info:
    # we will build workspace for each project
    os.chdir(work_path)
    if os.path.exists(project):
        os.system("rm -fr {}".format(project))
        os.mkdir(project)
    else:
        os.mkdir(project)
    os.chdir(project)
    os.mkdir('data')
    os.mkdir('qc')
    os.chdir('data')
    cwd = os.getcwd()
    # create raw data link
    sample_info = all_info[project]
    for sample in sample_info:
        new_name = sample_info[sample][2]
        os.system('echo "{}\t{}" >> ../qc/rawfqdir.list'.format(new_name, '../data/'+new_name))
        os.mkdir(new_name)
        os.chdir(new_name)
        lane_ids = sample_info[sample][0]
        abs_paths = sample_info[sample][1]
        i = 0
        for lane_id, each_path in zip(lane_ids, abs_paths):
            # more matching mode may be added in the following
            if (each_path.endswith("R1.fastq.gz") or
                each_path.endswith("R1_001.fastq.gz") or
                each_path.endswith("R1.fq.gz")):
                i += 1
                os.system('ln -s {} {}'
                          .format(each_path, new_name + '_data' + str(i) + '_' + lane_id + '_R1_001.fastq.gz'))
            elif (each_path.endswith("R2.fastq.gz") or
                  each_path.endswith("R2_001.fastq.gz") or
                  each_path.endswith("R2.fq.gz")):
                os.system('ln -s {} {}'
                          .format(each_path, new_name + '_data' + str(i) + '_' + lane_id + '_R2_001.fastq.gz'))
            else:
                print(each_path, '-> Cannot be parsed, check it or improve the program by changing searching mode')
        os.chdir(cwd)

print("Please check data carefully! Then go to the qc dir to qsub task with:"
      "\n nohup RNAseq_ToolBox_v1410 filter rawfqdir.list & ")


