import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load.py')).read())
import statistics as st, math
# A: training-free noise-rate estimate per client from zero-shot calibration
def est(rows,m,k):
    n=len(rows)
    py=[x[IX[m+'_py']] for x in rows]; s=[x[IX[m+'_sumsq']] for x in rows]
    S=sum(s)/n; P=sum(py)/n; c=(1-S)/(k-1)
    soft=(S-P)/(S-c)
    a=sum(x[IX[m+'_pred']]==x[0] for x in rows)/n; al=sum(x[IX[m+'_pmax']] for x in rows)/n
    hard=(al-a)/(al-(1-al)/(k-1))
    # standard error of soft estimate (per-image terms)
    t=[(si-pi)/(S-c) for si,pi in zip(s,py)]
    se=st.pstdev(t)/math.sqrt(n)
    return soft,hard,se
for ds in K:
  for sc in ("sym","pair","inst","het","clean"):
    res=collections.defaultdict(list)
    for f in runs(ds,sc):
      d=load(f)
      for r in d:
        if r<25: continue
        for c,rows in d[r].items():
          true=sum(x[0]!=x[1] for x in rows)/len(rows)
          for m in 'zge':
            soft,hard,se=est(rows,m,K[ds])
            res[(m,'honest' if true==0 else 'noisy')].append((true,soft,hard,se))
    print(f"== {ds} {sc}")
    for (m,ct),v in sorted(res.items()):
      tr=st.fmean(a for a,_,_,_ in v); so=st.fmean(b for _,b,_,_ in v); ha=st.fmean(c for _,_,c,_ in v)
      mae=st.fmean(abs(b-a) for a,b,_,_ in v); sig=st.fmean((b/d if d>0 else 0)>1.645 for _,b,_,d in v)
      print(f"   {m} {ct:6s} true {tr:.3f} | soft est {so:.3f} (MAE {mae:.3f}, flagged by z-test {sig:.2f}) | hard est {ha:.3f}")
