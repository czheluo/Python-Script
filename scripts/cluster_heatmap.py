"""
Cluster for gene expression data
"""
from __future__ import print_function
import numpy as np
#import fastcluster  # http://danifold.net/fastcluster.html?section=0
from scipy.cluster import hierarchy as sch
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors  # used in heatMap
from colorsys import hls_to_rgb
__author__ = 'gdq'


def cluster_heatmap(sample_values, expect_group=None, fig_name='HeatCluster', fig_size=(8, 9),
                    dpi=301, cluster_gene=False, cluster_sample=True, label_gene=False,
                    label_sample=True, display_gene_cluster=True, rotation=45, method='average',
                    metric='euclidean'):
    """
    :param sample_values: sample_values: name of text file/array which provide data with row header
    and column header; row headercontains gene symbol,while column header contains sample names.
    :param expect_group: a dictionary indicating expected grouping,keys are group names, values are
    lists of sample names.
    :param fig_name: the name of final figure
    :param fig_size: a tuple, figure size (width, height)
    :param dpi: resolution
    :param cluster_gene: boolean variable, if cluster gene?
    :param cluster_sample: boolean variable, if cluster sample?
    :param label_gene: boolean variable, if display gene symbols?
    :param label_sample: boolean variable, if display sample names?
    :param display_gene_cluster:
    :param rotation: rotation degree of sample labels
    :param method: method of hierarchy cluster,'average','median','single','centroid'
    :param metric:
    :return: A figure will be saved to the current directory
    """

    if sample_values not in locals().keys():
        print('-> Hi, we will get data from file:', sample_values)
        data_array = np.genfromtxt(sample_values, comments=None, dtype=None, delimiter='\t')
    else:
        data_array = sample_values
    sample_names = data_array[0, 1:]
    samples_groups = sample_names
    sample_number = len(sample_names)
    gene_symbols = data_array[1:, 0]
    gene_number = len(gene_symbols)
    for i in range(sample_number):
        # this process is designed for txt file from our team work
        if '](normalized)' in sample_names[i]:
            sample_name = sample_names[i]
            sample_group = sample_name.strip('(normalized)')
            samples_groups[i] = sample_group
            sample_name = sample_name.strip('[')
            sample_name = sample_name.strip('](normalized)')
            sample_names[i] = sample_name.split(',')[0]
    print('We know that sample names are:', sample_names)
    print('gene number is:', gene_number)
    data = np.array(data_array[1:, 1:], dtype=float)
    # 1. Cluster analysis and draw hierarchy tree
    left, bottom, width, height = 0.1, 0.1, 0.8, 0.8
    plt.figure(fig_name, fig_size)
    if label_gene:
        width -= 0.15
    else:
        width -= 0.04
    if cluster_gene:
        left += 0.15
        width -= 0.05
    # 1.1 Cluster sample
    if cluster_sample:
        height -= 0.1
        zgene = sch.linkage(np.transpose(data), method=method, metric=metric)
        if expect_group:
            plt.axes([left, 0.825, width, 0.18])
        else:
            plt.axes([left, 0.805, width, 0.18])
        plt.axis('off')
        hcluster_sample = sch.dendrogram(zgene)
        index = hcluster_sample['leaves']
        sample_names = sample_names[index]
        samples_groups = np.array(samples_groups)
        samples_groups = samples_groups[index]
        data = data[:, index]
    # 1.1.1 Draw a colorbar specifying expected grouping
    if expect_group:
        # Get random color pool
        color_number = len(expect_group.keys())
        colorpool = []
        for i in np.arange(60., 300., 300. / color_number):
            hue = i/300.
            randnumber = np.random.random_sample()
            lightness = (50 + randnumber * 10)/100.
            saturation = (90 + randnumber * 10)/100.
            colorpool.append(hls_to_rgb(hue, lightness, saturation))
        # Distribute color according to sample_infor
        sample_colors = {}
        i = -1
        for group in expect_group.keys():
            i += 1
            for each_sample in expect_group[group]:
                sample_colors[each_sample] = colorpool[i]
        colors = []
        for sample in sample_names:
            colors.append(sample_colors[unicode(sample)])
        # Begin to plot bar
        group_bar = plt.axes([left, 0.805, width, 0.015])
        plt.axis('off')
        group_bar.bar(range(sample_number), np.ones(sample_number), width=1, color=colors)
    # 1.2 Cluster gene
    if cluster_gene:
        zsample = sch.linkage(data, method=method, metric=metric)
        # zsample = sch.linkage(data, method=method, metric=metric)
        if display_gene_cluster:
            plt.axes([0.01, bottom, 0.235, height])
            plt.axis('off')
            hcluster_gene = sch.dendrogram(zsample, orientation='right',
                                           distance_sort=True, count_sort='ascending')
        else:
            hcluster_gene = sch.dendrogram(zsample, distance_sort=True, count_sort='ascending',
                                           no_plot=True)
        gene_order = hcluster_gene['leaves']
        gene_symbols = gene_symbols[gene_order]
        data = data[gene_order, :]  # adjust data rank
    # 2.0 Plot heat map
    matrix = plt.axes([left, bottom, width, height])
    matrix.autoscale(tight=True)
    # 2.1 Display sample name
    if label_sample:
        matrix.set_xticks(np.arange(sample_number) + 0.5)
        matrix.set_xticklabels(samples_groups, rotation=rotation, fontsize=9)
    else:
        matrix.set_xticks([])
        matrix.set_xticklabels([])
    # 2.2 Display gene name, and note that only 20 length of name will be displayed
    if label_gene:
        new_symbols = []
        for eachSymbol in gene_symbols:
            if len(eachSymbol) > 20:
                new_symbols.append(eachSymbol[0:20])
            else:
                new_symbols.append(eachSymbol)
        matrix.yaxis.tick_right()
        matrix.set_yticks(np.arange(gene_number)+0.5)
        tickline = matrix.get_yticklines()
        for line in tickline:
            line.set_visible(False)
            matrix.set_yticklabels(new_symbols, fontsize=6)
        print(new_symbols)
    else:  # not to display genSymbol
        matrix.set_yticks([])
        matrix.set_yticklabels([])
    # 2.3 Self-defined colormap, red-black-green
    cdict = {'red': ((0.0, 0.0, 0.0), (0.5, 0.0, 0.1), (1.0, 1.0, 1.0)),
             'blue': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
             'green': ((0.0, 0.0, 1.0), (0.5, 0.1, 0.0), (1.0, 0.0, 0.0))}
    my_cmap = mcolors.LinearSegmentedColormap('my_cmap', cdict, 256)
    # 2.4 Draw heat map
    sorted_data = sorted(data.flatten())
    data_number = len(sorted_data)
    mincolor = sorted_data[int(round(data_number*0.1))]
    maxcolor = sorted_data[int(round(data_number*0.9))]
    print('color Range:', mincolor, 'to', maxcolor)
    im = matrix.pcolormesh(data, cmap=my_cmap, vmin=mincolor, vmax=maxcolor)
    # 2.5 Draw colorbar in the ax of colorbar in appropriate position
    if label_gene:
        colorbar = plt.axes([left + width + 0.12, bottom, 0.02, height])
    else:
        colorbar = plt.axes([left + width + 0.01, bottom, 0.02, height])
    cbar = plt.colorbar(im, cax=colorbar, spacing='proportional')
    cbar.ax.tick_params(labelsize=8)
    # 3. Save figure
    plt.savefig(fig_name, dpi=dpi, bbox_inches='tight')
    plt.close('all')

# test
group_infor = {}
cluster_heatmap('heatmap.txt', expect_group=group_infor, fig_name='cluster', label_gene=False,
                cluster_gene=True, label_sample=True, cluster_sample=True, method='average',
                rotation=90, fig_size=(8, 12))


