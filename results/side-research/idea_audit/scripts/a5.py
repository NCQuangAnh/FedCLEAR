import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load.py')).read())
import statistics as st, math
def rho(rows,k):
    n=len(rows); py=[x[IX['z_py']] for x in rows]; s=[x[IX['z_sumsq']] for x in rows]
    S=sum(s)/n; P=sum(py)/n; c=(1-S)/(k-1); t=[(si-pi)/(S-c) for si,pi in zip(s,py)]
    return (S-P)/(S-c), st.pstdev(t)/math.sqrt(n)
def apply(rows,idx):
    # relabel to mix argmax if sure (>=0.5) and different, else drop; returns (wrong kept, correct kept, fixed, broken)
    out=[]; fixed=broken=0
    for i,x in enumerate(rows):
        lab=x[0]
        if i in idx:
            if x[IX['e_pmax']]>=0.5 and x[IX['e_pred']]!=lab:
                new=x[IX['e_pred']]; fixed+=(lab!=x[1] and new==x[1]); broken+=(lab==x[1] and new!=x[1]); lab=new
            else: continue
        out.append(lab==x[1])
    return sum(not o for o in out), sum(out), fixed, broken
print("after repair, whole federation, rounds 25-45 (per round avg): wrong labels kept | correct labels kept   [before: wrong | correct]")
for ds in K:
  for sc in ("sym","pair","inst","het","clean"):
    A=collections.defaultdict(lambda:[0,0,0,0]); base=[0,0]; nr=0
    for f in runs(ds,sc):
      nf=f.replace('diag_samples_seed_','noise_seed_')
      dg={r['round']:r['clients'] for r in json.load(open(nf))['diag']}
      d=load(f)
      for r in d:
        if r<25 or r>45 or r not in dg: continue
        nr+=1
        for c,rows in d[r].items():
          n=len(rows); base[0]+=sum(x[0]!=x[1] for x in rows); base[1]+=sum(x[0]==x[1] for x in rows)
          rec=dg[r].get(str(c)) or dg[r].get(c)
          order=sorted(range(n),key=lambda i:rows[i][IX['e_py']])
          rules={}
          # CLEAR as run: flag e.xs_m>0.05, suspects e_py<0.1, cap 60%
          if rec['e']['xs_m']>0.05:
            sus=[i for i in order if rows[i][IX['e_py']]<0.1]; rules['CLEAR']=set(sus[:int(0.6*n)]); rules['CLEAR_nocap']=set(sus)
          else: rules['CLEAR']=set(); rules['CLEAR_nocap']=set()
          rh,se=rho(rows,K[ds])
          b=max(0,round(rh*n)); flag=se>0 and rh/se>1.645
          rules['audit_budget']=set(order[:b]) if flag else set()      # z-test flag, budget = estimated noise count
          rules['audit_budget_all']=set(order[:b])                     # no flag at all: every client repairs its estimate
          for k_,s in rules.items():
            w,cc,fx,br=apply(rows,s); a=A[k_]; a[0]+=w; a[1]+=cc; a[2]+=fx; a[3]+=br
    print(f"== {ds} {sc}: before {base[0]/nr:.1f} | {base[1]/nr:.1f}")
    for k_,a in A.items():
      print(f"   {k_:17s} wrong {a[0]/nr:6.1f} | correct {a[1]/nr:6.1f}   (fixed {a[2]/nr:.1f}, broken {a[3]/nr:.1f})")
