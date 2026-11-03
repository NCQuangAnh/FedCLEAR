import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load.py')).read())
import statistics as st
def auroc(pos,neg):
    # P(score_noisy > score_clean); scores = -P(label)
    allv=sorted([(v,1) for v in pos]+[(v,0) for v in neg]); r=0; rank=0; npos=len(pos); nneg=len(neg)
    # rank-sum with ties averaged
    i=0; ranks=[]
    while i<len(allv):
        j=i
        while j<len(allv) and allv[j][0]==allv[i][0]: j+=1
        avg=(i+j+1)/2
        for k in range(i,j): ranks.append((avg,allv[k][1]))
        i=j
    rs=sum(a for a,l in ranks if l==1)
    return (rs-npos*(npos+1)/2)/(npos*nneg)
print("per-image ranking inside noisy clients (AUROC, score = -P(label)); triangulation Z=G!=L: recall / precision / relabel-correct")
for ds in K:
  for sc in ("sym","pair","inst","het"):
    S=collections.defaultdict(lambda:([],[])); tri=collections.Counter()
    for f in runs(ds,sc):
      d=load(f)
      for r in d:
        if r<25 or r>45: continue
        lab_cnt=collections.Counter(x[0] for c in d[r] for x in d[r][c])
        for c,rows in d[r].items():
          if all(x[0]==x[1] for x in rows): continue
          own=collections.Counter(x[0] for x in rows)
          for x in rows:
            nz=x[0]!=x[1]; s=own[x[0]]/lab_cnt[x[0]]
            sc_={'z':-x[IX['z_py']],'g':-x[IX['g_py']],'e':-x[IX['e_py']],
                 'own':-(s*x[IX['z_py']]+(1-s)*x[IX['g_py']])}
            for k_,v in sc_.items(): S[k_][0 if nz else 1].append(v)
            agree=x[IX['z_pred']]==x[IX['g_pred']]!=x[0]
            tri['noisy']+=nz; tri['flag']+=agree; tri['tp']+=agree and nz; tri['fix']+=agree and x[IX['z_pred']]==x[1]
    print(f"  {ds:11s} {sc:5s} " + "  ".join(f"{k_} {auroc(*S[k_]):.3f}" for k_ in ('z','g','e','own')) +
          f"   | tri recall {tri['tp']/tri['noisy']:.2f} prec {tri['tp']/max(tri['flag'],1):.2f} relabel-ok {tri['fix']/max(tri['flag'],1):.2f}")
