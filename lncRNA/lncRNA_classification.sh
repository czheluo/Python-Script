for i in `ls *gtf`
do
perl /mnt/ilustre/users/zhuo.wen/scripts/lncRNA/Classification_list.pl $i $i.list
awk '{print $0}' $i.list |sort -u|cut -f 2|sort|uniq -c > $i.list.stat.txt
done

#filter1--assembly iux selected gtf
#filter3--before advanced softwares filter
#filter4--after advanced softwares filtered 

paste filter1.gtf.list.stat.txt filter3.gtf.list.stat.txt filter4.gtf.list.stat.txt | awk -F " " 'BEGIN{OFS="\t"; print "type","Assembly","Basic_filter","Advanced_filter"}{print $2,$1,$3,$5}' > lncRNA_classification.xls

perl /mnt/ilustre/users/zhuo.wen/scripts/lncRNA/lncRNA_classification_barplot.pl lncRNA_classification.xls
#Rscript /mnt/ilustre/users/zhuo.wen/scripts/lncRNA/lncRNA_classification_barplot.r


