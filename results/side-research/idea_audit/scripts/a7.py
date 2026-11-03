import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load.py')).read())
import statistics as st
# (1) bias of the global-model auditor on HONEST clients vs how much noise the federation holds; zero-shot for contrast
print("estimate on honest clients (true 0), rounds 25-45:  global g | mix e | zero-shot z")
for ds in K:
  row=[]
  for sc in ("clean","sym","pair","het"):
    v=collections.defaultdict(list)
    for f in runs(ds,sc):
      d=load(f)
      for r in d:
        if r<25 or r>45: continue
        for c,rows in d[r].items():
          if any(x[0]!=x[1] for x in rows): continue
          n=len(rows)
          for m in 'gez':
            S=sum(x[IX[m+'_sumsq']] for x in rows)/n; P=sum(x[IX[m+'_py']] for x in rows)/n; cc=(1-S)/(K[ds]-1)
            v[m].append((S-P)/(S-cc))
    row.append(f"{sc}: {st.fmean(v['g']):+.2f} | {st.fmean(v['e']):+.2f} | {st.fmean(v['z']):+.2f}")
  print(f"  {ds:11s} "+"   ".join(row))
# (2) relabel accuracy on truly noisy images when the source is >=50% sure
print("relabel accuracy on noisy images when source top prob >= 0.5 (share of noisy images covered)")
for ds in K:
  for sc in ("sym","pair"):
    a=collections.Counter()
    for f in runs(ds,sc):
      d=load(f)
      for r in d:
        if r<25 or r>45: continue
        for c,rows in d[r].items():
          for x in rows:
            if x[0]==x[1]: continue
            a['n']+=1
            for m in 'gez':
              if x[IX[m+'_pmax']]>=0.5 and x[IX[m+'_pred']]!=x[0]:
                a[m]+=1; a[m+'ok']+=x[IX[m+'_pred']]==x[1]
    print(f"  {ds:11s} {sc:5s} "+"  ".join(f"{m}: {a[m+'ok']/max(a[m],1):.2f} ({a[m]/a['n']:.2f})" for m in 'gez'))
