#!/usr/bin/env python
import subprocess
import sys
import time
from itertools import imap, chain, izip
from collections import defaultdict

def rsquared(x, y):
  # Drop observations that are None or NaN. 
  good_is = []
  for i in xrange(len(x)):
    if (x[i] is not None) and (y[i] is not None):
      good_is.append(i)

  x = [x[i] for i in good_is]
  y = [y[i] for i in good_is]

  n = len(x)

  sum_x = float(sum(x))
  sum_y = float(sum(y))

  sum_x_sq = sum(map(lambda x: pow(x, 2), x))
  sum_y_sq = sum(map(lambda x: pow(x, 2), y))

  psum = sum(imap(lambda x, y: x * y, x, y))
  num = psum - (sum_x * sum_y/n)
  den = pow((sum_x_sq - pow(sum_x, 2) / n) * (sum_y_sq - pow(sum_y, 2) / n), 0.5)

  if den == 0: return 0

  return pow(num / den,2)

def geno_to_code(g):
  g = g[0] + g[2]
  if '.' in g:
    return None
  elif g == '00':
    return 0
  elif g == '01':
    return 1
  elif g == '10':
    return 1
  elif g == '11':
    return 2
  else:
    raise Exception, "Error: genotypes from VCF have more than 4 possible states (more than 2 ordered alleles.)"

def haplo_to_code(g):
  if g[1] != "|":
    raise Exception, "Error: unable to calculate D or D' since genotypes are not phased"

  try:
    g0 = int(g[0])
  except:
    g0 = None

  try:
    g1 = int(g[2])
  except:
    g1 = None

  if g0 != None and g0 > 1:
    raise Exception, "Error: more than 2 alleles when trying to calculate LD!"

  if g1 != None and g1 > 1:
    raise Exception, "Error: more than 2 alleles when trying to calculate LD!"

  return [g0,g1]

def ld_rsquare_indexsnp_vcf(index_pos,vcf_file,region,tabix_path="tabix",ignore_filter=False):
  # First grab the index SNP's genotypes. 
  chrom = region.split(":")[0]
  if not int(index_pos) >= 0:
    print >> sys.stderr, "Error computing LD: index SNP position %s is invalid.." % str(index_pos)
    return

  index_region = "{0}:{1}-{1}".format(chrom,index_pos)

  if 'chr' not in chrom:
    chrom = 'chr' + chrom

  index_chrpos = "{0}:{1}".format(chrom,index_pos)

  p = subprocess.Popen([tabix_path,vcf_file,index_region],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  (stdout,stderr) = p.communicate()

  if stdout == '':
    print >> sys.stderr, "Error: while calculating LD from VCF file: index SNP position %s does not exist in file.. " % str(index_pos)
    return

  if stderr != '':
    print >> sys.stderr, "Error: while calculating LD from VCF file: tabix generated an error: \n%s" % stderr
    return

  index_rec = stdout.rstrip().split("\t")
  try:
    index_gts = map(geno_to_code,index_rec[9:])
  except Exception as e:
    # If we're here, either: 
    # 1) the index SNP was not biallelic, or
    # 2) the index SNP had genotypes that were not phased
    print >> sys.stderr, e.message
    return None

  (index_ref,index_alt) = index_rec[3:5]

#  if len(index_ref) != 1:
#    print >> sys.stderr, "Error: while calculating LD from VCF file: index SNP is not a SNP - ref allele was %s, alt allele was %s" % (index_ref,index_alt)
#    return
#
#  if len(index_alt) != 1:
#    print >> sys.stderr, "Error: while calculating LD from VCF file: index SNP is not a SNP - ref allele was %s, alt allele was %s" % (index_ref,index_alt)
#    return

  # Now grab the other SNPs, and calculate r2 with each of them. 
  p = subprocess.Popen([tabix_path,vcf_file,region],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  (stdout,stderr) = p.communicate()
  
  if stderr != '':
    print >> sys.stderr, "Error: while calculating LD from VCF file: tabix generated an error: \n%s" % stderr
    return

  # Create a temporary file to write LD to. 
  ld_filename = "templd_%s_%s_%s-%s.txt" % (
    chrom,
    index_pos,
    time.strftime("%y%m%d",time.localtime()),
    time.strftime("%H%M%S",time.localtime())
  )

  seen = {}
  markers = 0
  with open(ld_filename,'w') as out:
    print >> out, "\t".join(['snp1','snp2','dprime','rsquare'])

    results = []
    records = stdout.split("\n")
    for rec in records:
      if rec == '' or rec == None:
        continue

      rec = rec.split("\t")
      rec[-1] = rec[-1].rstrip()

#     Commented out for plotting indels that are biallelic
#      # Is this a SNP? 
#      (rec_ref,rec_alt) = rec[3:5]

#      if len(rec_ref) != 1:
#        continue
#      elif len(rec_alt) != 1:
#        continue

      # Did it pass filters? 
      if not ignore_filter:
        rec_pass = rec[6]
        if rec_pass != "PASS":
          continue

      # SNP/chr/pos
      (chr,pos,snp) = rec[0:3]
      if 'chr' not in chr:
        chr = 'chr' + chr
      chrpos = "{0}:{1}".format(chr,pos)

      if pos == index_pos:
        continue

      # Have we seen this variant already? 
      if seen.get((chr,pos)) is not None:
        print >> sys.stderr, "Warning: multiple variants at same position (%s) in VCF file, using the first variant" % chrpos
        continue
      else:
        seen[(chr,pos)] = 1

      # Genotypes, converted to 0/1/2 coding
      try:
        gts = map(geno_to_code,rec[9:])
      except:
        continue

      # Calculate r2. 
      rsq = rsquared(index_gts,gts)

      # Write out in the format expected by locuszoom. 
      print >> out, "\t".join([chrpos,index_chrpos,"NA",str(rsq)])

      markers += 1

  if markers == 0:
    print >> sys.stderr, "Error: no valid markers in VCF file to compute LD from.."
    return

  return ld_filename

# Wrapper function for calculating LD. 
# method can be 'rsquare' or 'dprime'
# Called like: 
# ld_from_vcf('rsquare',index_pos,vcf_file,region,tabix_path='tabix')
def ld_from_vcf(method,*args,**kargs):
  if method == 'rsquare':
    return ld_rsquare_indexsnp_vcf(*args,**kargs)
  elif method == 'dprime':
    return ld_dprime_indexsnp_vcf(*args,**kargs)
  else:
    raise Exception, "Error: only 'rsquare' and 'dprime' methods available for calculating LD from VCF file."

def ld_dprime_indexsnp_vcf(index_pos,vcf_file,region,tabix_path="tabix",ignore_filter=False):
  # First grab the index SNP's genotypes. 
  chrom = region.split(":")[0]
  if not int(index_pos) >= 0:
    print >> sys.stderr, "Error computing LD: index SNP position %s is invalid.." % str(index_pos)
    return

  index_region = "{0}:{1}-{1}".format(chrom,index_pos)

  if 'chr' not in chrom:
    chrom = 'chr' + chrom

  index_chrpos = "{0}:{1}".format(chrom,index_pos)

  p = subprocess.Popen([tabix_path,vcf_file,index_region],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  (stdout,stderr) = p.communicate()

  if stdout == '':
    print >> sys.stderr, "Error: while calculating LD from VCF file: index SNP position %s does not exist in file.. " % str(index_pos)
    return

  if stderr != '':
    print >> sys.stderr, "Error: while calculating LD from VCF file: tabix generated an error: \n%s" % stderr
    return

  # Insert index SNP phased genotypes into list in order 
  index_rec = stdout.rstrip().split("\t")
  try:
    index_gts = [g for g in chain.from_iterable(map(haplo_to_code,index_rec[9:]))]
  except Exception as e:
    # If we're here, either: 
    # 1) the index SNP was not biallelic, or
    # 2) the index SNP had genotypes that were not phased
    print >> sys.stderr, e.message
    return None

  (index_ref,index_alt) = index_rec[3:5]

  if len(index_ref) != 1:
    print >> sys.stderr, "Error: while calculating LD from VCF file: index SNP is not a SNP - ref allele was %s, alt allele was %s" % (index_ref,index_alt)
    return

  if len(index_alt) != 1:
    print >> sys.stderr, "Error: while calculating LD from VCF file: index SNP is not a SNP - ref allele was %s, alt allele was %s" % (index_ref,index_alt)
    return

  # Now grab the other SNPs, and calculate r2 with each of them. 
  p = subprocess.Popen([tabix_path,vcf_file,region],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  (stdout,stderr) = p.communicate()
  
  if stderr != '':
    print >> sys.stderr, "Error: while calculating LD from VCF file: tabix generated an error: \n%s" % stderr
    return

  # Create a temporary file to write LD to. 
  ld_filename = "templd_%s_%s_%s-%s.txt" % (
    chrom,
    index_pos,
    time.strftime("%y%m%d",time.localtime()),
    time.strftime("%H%M%S",time.localtime())
  )

  seen = {}
  markers = 0
  with open(ld_filename,'w') as out:
    print >> out, "\t".join(['snp1','snp2','dprime','rsquare'])

    results = []
    records = stdout.split("\n")
    for rec in records:
      if rec == '' or rec == None:
        continue

      rec = rec.split("\t")
      rec[-1] = rec[-1].rstrip()

#     Commented out for LD with biallelic indels
#      # Is this a SNP? 
#      (rec_ref,rec_alt) = rec[3:5]

#      if len(rec_ref) != 1:
#        continue
#      elif len(rec_alt) != 1:
#        continue

      # Did it pass filters? 
      if not ignore_filter:
        rec_pass = rec[6]
        if rec_pass != "PASS":
          continue

      # SNP/chr/pos
      (chr,pos,snp) = rec[0:3]
      if 'chr' not in chr:
        chr = 'chr' + chr
      chrpos = "{0}:{1}".format(chr,pos)

      if pos == index_pos:
        continue

      # Have we seen this variant already? 
      if seen.get((chr,pos)) is not None:
        print >> sys.stderr, "Warning: multiple variants at same position (%s) in VCF file, using the last variant" % chrpos
      else:
        seen[(chr,pos)] = 1

      # Phased genotypes inserted into array in order 
      try:
        gts = [g for g in chain.from_iterable(map(haplo_to_code,rec[9:]))]
      except:
        # If this SNP is either not biallelic or has unphased genotypes, skip it
        continue

      # Number of non-missing alleles
      nonmiss_gts = sum(map(lambda x: x is not None,gts))

      # Calculate statistics from haplos
      counts = defaultdict(int)
      nonmiss_haplos = 0.0
      index_afs = [0,0]
      afs = [0,0]
      for haplo in izip(index_gts,gts):
        if None in haplo:
          continue

        counts[haplo] = counts[haplo] + 1
        index_afs[haplo[0]] += 1
        afs[haplo[1]] += 1
        nonmiss_haplos += 1

      # Normalize allele frequencies
      index_afs = map(lambda x: x / nonmiss_haplos,index_afs)
      afs = map(lambda x: x / nonmiss_haplos,afs)

      # Normalize haplo counts
      hfreq = defaultdict(int)
      for k,v in counts.iteritems():
        hfreq[k] = v / nonmiss_haplos

      # D statistic
      d_stat = (hfreq[(0,0)]*hfreq[(1,1)] - hfreq[(1,0)]*hfreq[(0,1)])

      # D' statistic
      if d_stat < 0:
        d_max = max(-1 * index_afs[0] * afs[0], -1 * index_afs[1] * afs[1])
        d_prime = d_stat / d_max
      elif d_stat > 0:
        d_max = min(index_afs[0] * afs[1], index_afs[1] * afs[0])
        d_prime = d_stat / d_max
      else:
        d_prime = d_stat

      # Write out in the format expected by locuszoom. 
      print >> out, "\t".join([chrpos,index_chrpos,str(d_prime),"NA"])

      markers += 1

      #import pdb
      #pdb.set_trace()

  if markers == 0:
    print >> sys.stderr, "Error: no valid markers in VCF file to compute LD from.."
    return

  return ld_filename
