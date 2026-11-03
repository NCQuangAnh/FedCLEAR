import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load.py')).read())
import statistics as st, math
# budget from the estimate itself (audit) vs from its upper 95% bound (audit_ucb); CLEAR as run for reference
def rho(rows,k):
    n=len(rows); py=[x[IX['z_py']] for x in rows]; s=[x[IX['z_sumsq']] for x in rows]
    S=sum(s)/n; P=sum(py)/n; c=(1-S)/(k-1); t=[(si-pi)/(S-c) for si,pi in zip(s,py)]
    return (S-P)/(S-c), st.pstdev(t)/math.sqrt(n)
def apply(rows,idx):
    out=[]
    for i,x in enumerate(rows):
        lab=x[0]
        if i in idx:
            if x[IX['e_pmax']]>=0.5 and x[IX['e_pred']]!=lab: lab=x[IX['e_pred']]
            else: continue
        out.append(lab==x[1])
    return sum(not o for o in out), sum(out)
print("wrong labels left | correct labels kept, per round, rounds 25-45")
for ds in K:
  for sc in ("sym","pair","inst","het","clean"):
    A=collections.defaultdict(lambda:[0,0]); nr=0; se_all=[]
    for f in runs(ds,sc):
      dg={r['round']:r['clients'] for r in json.load(open(f.replace('diag_samples_seed_','noise_seed_')))['diag']}
      d=load(f)
      for r in d:
        if r<25 or r>45 or r not in dg: continue
        nr+=1
        for c,rows in d[r].items():
          n=len(rows); rec=dg[r].get(str(c)) or dg[r].get(c)
          order=sorted(range(n),key=lambda i:rows[i][IX['e_py']])
          sus=[i for i in order if rows[i][IX['e_py']]<0.1]
          rh,se=rho(rows,K[ds]); se_all.append(se); flag=se>0 and rh/se>1.645
          R={'CLEAR':set(sus[:int(0.6*n)]) if rec['e']['xs_m']>0.05 else set(),
             'audit':set(order[:max(0,round(rh*n))]) if flag else set(),
             'audit_ucb':set(order[:min(n,round((rh+1.645*se)*n))]) if flag else set()}
          for k_,s in R.items():
            w,cc=apply(rows,s); A[k_][0]+=w; A[k_][1]+=cc
    print(f"  {ds:11s} {sc:5s} se~{st.fmean(se_all):.3f}  " + "   ".join(f"{k_} {a[0]/nr:5.1f} | {a[1]/nr:5.1f}" for k_,a in A.items()))
