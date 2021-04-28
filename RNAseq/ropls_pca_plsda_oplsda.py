#!/usr/bin/env python
#coding:utf-8
#xianhongdai
#20191014

import argparse
import os 
import sys
sys.path.append('/mnt/ilustre/users/hui.wan/.local/lib/python2.7/site-packages/Mako-1.0.6-py2.7.egg') 
from mako.template import Template

parser = argparse.ArgumentParser( description="pca-plsda-oplsda-analyse-use-ropls")
parser.add_argument( "-i", dest="file",required=True, type=str, help="please input data matrix file")
parser.add_argument( "-g", dest="group",required=True, type=str, help="please input group file")
parser.add_argument( "-ci", dest="ci", type=str, default = '0.95', help="Hotteling's T2 confidence level ,defalt: 0.95")
parser.add_argument( "-perm", dest="perm", type=str, default = '200', help='the number of permutation test,defalt: 200')
parser.add_argument( "-anal", dest="anal", type=str, default = 'plsda', help='the analyse type pca plsda oplsda,default: plsda')
parser.add_argument( "-scale", dest="scale", type=str, default = 'Par', help='the method of data scale Par,UV,Ctr ,none,default:Par')
parser.add_argument( "-log", dest="log", type=str, default = 'TRUE', help=' whether the data should be transformed,default:TRUE')
parser.add_argument( "-show", dest="show", type=str, default = '1', help='show the sample name; 0 not show the sample name, default:1')
parser.add_argument( "-ell", dest="ell", type=str, default = 'group', help='the type of ellipse group or all,default:group')
parser.add_argument( "-draw_3d", dest="draw_3d", type=str, default = 'no', help='wheather to draw three dim plot,default:no')
parser.add_argument( "-o", dest="o", type=str,required=True, help='out_name prefix')
args = parser.parse_args()
Rcmd=r'''options(warn=-1)
library("ropls")
mymethod <- paste("/mnt/ilustre/centos7users/xianhong.dai/workspace/script", "PlotPLS2DScore.r",sep="/")
source(mymethod)
mymethod_3d <- paste("/mnt/ilustre/centos7users/xianhong.dai/workspace/script", "Plot3D.R",sep="/")
source(mymethod)
mymethod_3d_1 <- paste("/mnt/ilustre/centos7users/xianhong.dai/workspace/script", "PlotPLS3DScore.r",sep="/")
source(mymethod)
source(mymethod_3d)
source(mymethod_3d_1)

cdata <- read.table("${inputfile}", head = TRUE, sep = "\t", row.names = 1,quote='\"', na.strings = 'NA')
csif <- read.table("${groupfile}",header=T,sep="\t",comment.char = "",check.names = FALSE,row.names =1)
classFc <- as.factor(csif[,1])
cdata <- cdata[which(rowSums(cdata)!=0),]
gsamp <- rownames(csif)
samp <- colnames(cdata)
cdata <- cdata[,which(samp %in% gsamp)]
cdata <- t(cdata)
cdata <- cdata[rownames(csif),]

draw_3d = "${draw_3d}"
if (draw_3d == "yes"){
    angl = 40}


ci <- strsplit("${ci}",";")[[1]]
permutation <- strsplit("${perm}",";")[[1]]
mul_type = strsplit("${mul_type}",";")[[1]]
scale = strsplit("${data_trans}",";")[[1]]
drawell = strsplit("${ell}",";")[[1]]
log = strsplit("${log}",";")[[1]]
if(length(gsamp) <7){
crossvalI = length(gsamp)
}else{
crossvalI = 7 # package default
}
# for plsda ,oplsda result table
get_pls_result <- function(pls_result, mytype, out_prefix,confidence){
        pls <- pls_result
        out_prefix <- paste(out_prefix,mytype,sep=".")
        name.pls.x <- paste(out_prefix,"sites.xls",sep=".")
        name.pls.loading <- paste(out_prefix,"loading.xls",sep=".")
        name.pls.vip <- paste(out_prefix,"vip.xls",sep=".")
        name.pls.sum <- paste(out_prefix,"model.xls",sep=".")
        name.pls.permMN<- paste(out_prefix,"permMN.xls",sep=".")
        name.pls.intercept <- paste(out_prefix,"intercept.xls",sep=".")
        name.pls.ellipse <- paste(out_prefix,"ellipse.xls",sep=".")
        pls.perMN <- pls@suppLs$permMN[,c(2,3,7)]
        pls.all_model <- (pls@modelDF)[,1:6]
        if(mytype=="PLS-DA"){
            pls.x <- getScoreMN(pls)
            pls.loading <- getLoadingMN(pls)
        }else{
            pls.p <- getScoreMN(pls)
            pls.o <- pls@orthoScoreMN
            pls.x <- cbind(pls.p,pls.o)
            pls.pl <- getLoadingMN(pls)
            pls.ol <- pls@orthoLoadingMN
            pls.loading <- cbind(pls.pl,pls.ol)
        }
        #pls.loading <- getLoadingMN(pls)
        pls.sum <- pls@modelDF
        pls.vip <- getVipVn(pls)
        pls.vip <- as.data.frame(pls.vip)
        colnames(pls.vip) <- "VIP"
        pls.z1 <- lm(pls.perMN[,1]~pls.perMN[,3])$coefficients[1]
        pls.z2 <- lm(pls.perMN[,2]~pls.perMN[,3])$coefficients[1]
        pls.z <- as.matrix(c(pls.z1,pls.z2))
        ellipse.data <- add_ellipse(pls,classFc,confidence)
        write.table(pls.x,name.pls.x,sep="\t",quote=F,col.names=NA)
        
        
        write.table(pls.loading,name.pls.loading,sep="\t",quote=F,col.names=NA)
        write.table(pls.vip,name.pls.vip,sep="\t",quote=F,col.names=NA)
        write.table(pls.sum,name.pls.sum,sep="\t",quote=F,col.names=NA)
        write.table(pls.z,name.pls.intercept,sep="\t",quote=F)
        write.table(ellipse.data,name.pls.ellipse,sep="\t",row.names=F,quote=F,col.names=T)
        write.table(pls.perMN,name.pls.permMN,sep="\t",row.names=F,quote=F)
}
# from mul_type get ci,perm,sacle value
get_function_var <- function(m_type,myvar,is_numeric=T){
    if(is_numeric){
    result <- as.numeric(myvar[which(mul_type == m_type )])
    }else{
     result <- myvar[which(mul_type == m_type )]
    }
    return(result)
}

# from scale abbreviation to scale method
get_scale <- function(abbreviation){
    if(abbreviation == "UV"){
        scale <- "standard"
    }else if(abbreviation =="Ctr"){
        scale <- "center"
    }else if(abbreviation == "Par"){
        scale <- "pareto"
    }else{
        scale <- "none"
    }
    return(scale)
}

if ("pca"  %in% mul_type){
        confidence <- get_function_var("pca",ci)
        trans <- get_function_var("pca",scale,is_numeric=F)
        ellipse <- get_function_var("pca",drawell,is_numeric=F)
        log <- get_function_var("pca",log,is_numeric=F)
        pca <- opls(cdata,printL=F,plotL=F,predI=NA,scaleC=get_scale(trans),crossvalI=crossvalI,log10L=(log==as.character(TRUE)))
        if(pca@summaryDF[["pre"]] <="2"){
            if(draw_3d == "no"){
                pca <- pca
        }else{
            pca <- opls(cdata,printL=F,plotL=F,predI=3,scaleC=get_scale(trans),crossvalI=crossvalI,log10L=(log==as.character(TRUE)))}
        }
        name.pca.x <- paste("${output}","PCA.sites.xls",sep=".")
        name.pca.loading <- paste("${output}","PCA.loading.xls",sep=".")
        name.pca.sum <- paste("${output}","PCA.model.xls",sep=".")
        name.pca.ellipse <- paste("${output}","PCA.ellipse.xls",sep=".")
        pca.x <- getScoreMN(pca)
        pca.loading <- getLoadingMN(pca)
        pca.sum <- pca@modelDF
        ellipse.data <- add_ellipse(pca,classFc,confidence)
        write.table(pca.x,name.pca.x,sep="\t",quote=F,col.names=NA)
        write.table(pca.loading,name.pca.loading,sep="\t",quote=F,col.names=NA)
        write.table(pca.sum,name.pca.sum,sep="\t",quote=F,col.names=NA)
        write.table(ellipse.data,name.pca.ellipse,sep="\t",row.names=F,quote=F,col.names=T)
        PlotPCA2DScore(pca,csif,"${output}", width=NA, ellipse,confidence, show=as.numeric("${show}"), grey.scale=0)
        if(draw_3d == "yes"){
        PlotPCA3DScore(pca,csif,"${output}",format="pdf", width=NA,angl)}
}
if("plsda" %in% mul_type){
        confidence <- get_function_var("plsda",ci)
        trans <- get_function_var("plsda",scale,is_numeric=F)
        log <- get_function_var("plsda",log,is_numeric=F)
        perm <- get_function_var("plsda",permutation)
        ellipse <- get_function_var("plsda",drawell,is_numeric=F)
        
        plsda <- opls(cdata,classFc,printL=F,plotL=F,predI=2,scaleC=get_scale(trans),permI=perm,crossvalI=crossvalI,log10L=(log==as.character(TRUE)))
        if(plsda@modelDF$Signif.[2] == "NS" | plsda@modelDF$Signif.[2] == "N4"| plsda@modelDF$Signif.[1] == "NS"|plsda@modelDF$Signif.[1] == "N4"){
            plsda <- opls(cdata,classFc,printL=F,plotL=F,predI=2,scaleC=get_scale(trans),permI=perm,crossvalI=crossvalI,log10L=(log==as.character(TRUE)))
        }else{
        plsda <- opls(cdata,classFc,printL=F,plotL=F,predI=NA,scaleC=get_scale(trans),permI=perm,crossvalI=crossvalI,log10L=(log==as.character(TRUE)))
        }
        if(plsda@summaryDF[["pre"]] <="2"){
            if(draw_3d == "no"){
                plsda <- plsda
            }else{
                plsda <- opls(cdata,classFc,printL=F,plotL=F,predI=3,scaleC=get_scale(trans),permI=perm,crossvalI=crossvalI,log10L=(log==as.character(TRUE)))}
        }   
        get_pls_result(plsda,"PLS-DA","${output}",confidence)
        PlotPLS2DScore(plsda,csif,"${output}", width=NA, ellipse, confidence, show=as.numeric("${show}"), grey.scale=0)
        
        PlotModelPerm(plsda,"${output}","PLS-DA")
        if(draw_3d == "yes"){
            PlotPLS3DScore(plsda,csif,"${output}",format="pdf", width=NA,angl)}
}
if("oplsda" %in% mul_type){
        confidence <- get_function_var("oplsda",ci)
        trans <- get_function_var("oplsda",scale,is_numeric=F)
        log <- get_function_var("oplsda",log,is_numeric=F)
        perm <- get_function_var("oplsda",permutation)
        ellipse <- get_function_var("oplsda",drawell,is_numeric=F)
        oplsda <- opls(cdata, classFc, predI=1, orthoI=1,printL=F,plotL=F,scaleC=get_scale(trans),permI=perm,crossvalI=crossvalI,log10L=(log==as.character(TRUE)))
        if(oplsda@modelDF[[1,"Signif."]] !="NS" & oplsda@modelDF[[2,"Signif."]] !="NS" & oplsda@modelDF[[1,"Signif."]] !="N4" & oplsda@modelDF[[2,"Signif."]] !="N4" ){
                oplsda <- opls(cdata,classFc,predI=1,orthoI=NA,printL=F,plotL=F,scaleC=get_scale(trans),permI=perm,crossvalI=crossvalI,log10L=(log==as.character(TRUE)))
        }
        if(oplsda@summaryDF[["ort"]] =="1"){
            if(draw_3d == "no"){
                oplsda <- oplsda
             }else{
                oplsda <- opls(cdata,classFc,printL=F,plotL=F,predI=1,orthoI=2,scaleC=get_scale(trans),permI=perm,crossvalI=crossvalI,log10L=(log==as.character(TRUE)))}
        }
        get_pls_result(oplsda,"OPLS-DA","${output}",confidence)
        PlotOPLS2DScore(oplsda,csif,"${output}", width=NA, ellipse,confidence, show= as.numeric("${show}"), grey.scale=0)
        PlotModelPerm(oplsda,"${output}","OPLS-DA")
        if(draw_3d == "yes"){
        PlotOPLS3DScore(oplsda,csif,"${output}",format="pdf", width=NA,angl)}
}'''

f = Template(Rcmd)
Rcmd = f.render(inputfile=args.file,groupfile=args.group,ci=args.ci,perm=args.perm,mul_type=args.anal,data_trans=args.scale,log=args.log,show=args.show,ell=args.ell,draw_3d = args.draw_3d,output=args.o)
fout=open('%s.%s.cmd.r' %(args.o,args.anal),'w')
fout.write(Rcmd)
fout.close()
cmd = 'Rscript %s.%s.cmd.r' %(args.o,args.anal)
os.system(cmd)

