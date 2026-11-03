import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load.py')).read())
import statistics as st, math
def rho(rows,k,m='z'):
    n=len(rows); py=[x[IX[m+'_py']] for x in rows]; s=[x[IX[m+'_sumsq']] for x in rows]
    S=sum(s)/n; P=sum(py)/n; c=(1-S)/(k-1); t=[(si-pi)/(S-c) for si,pi in zip(s,py)]
    return (S-P)/(S-c), st.pstdev(t)/math.sqrt(n)
# client-level detection: CLEAR (e.xs_m > 0.05, from diag records) vs zero-shot audit z-test (one-sided 5%)
print("client detection, rounds 25-50: [CLEAR flag rate honest / noisy]  vs  [audit z-test honest / noisy]")
for ds in K:
  for sc in ("sym","pair","inst","het","clean"):
    a=collections.Counter()
    for f in runs(ds,sc):
      nf=f.replace('diag_samples_seed_','noise_seed_')
      dg={r['round']:r['clients'] for r in json.load(open(nf))['diag']}
      d=load(f)
      for r in d:
        if r<25 or r not in dg: continue
        for c,rows in d[r].items():
          ct='h' if all(x[0]==x[1] for x in rows) else 'n'
          rec=dg[r].get(str(c)) or dg[r].get(c)
          a[ct]+=1
          if rec and rec['e']['xs_m']>0.05: a['clear_'+ct]+=1
          rh,se=rho(rows,K[ds]); 
          if se>0 and rh/se>1.645: a['aud_'+ct]+=1
    h,n=max(a['h'],1),max(a['n'],1)
    print(f"  {ds:11s} {sc:5s}  CLEAR {a['clear_h']/h:.2f} / {a['clear_n']/n if a['n'] else float('nan'):.2f}   audit {a['aud_h']/h:.2f} / {a['aud_n']/n if a['n'] else float('nan'):.2f}")
