import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load.py')).read())
import statistics as st
# consensus capture: does the global model adopt a noisy client's wrong labels more when that client holds most of the class?
for ds in K:
  for sc in ("pair","sym","inst"):
    bins=collections.defaultdict(lambda:[0,0,0.0,0.0,0])  # share bin -> n, adopted(g_pred==label), sum g_py, sum z_py, zs adopted
    for f in runs(ds,sc):
      d=load(f)
      r0=min(d); cnt=collections.Counter(x[1] for c in d[r0] for x in d[r0][c])
      for r in d:
        if r<25: continue
        for c,rows in d[r].items():
          own=collections.Counter(x[1] for x in rows)
          for x in rows:
            if x[0]==x[1]: continue
            s=own[x[1]]/cnt[x[1]]
            b=min(int(s*4),3)  # quarters of ownership of the TRUE class
            B=bins[b]; B[0]+=1; B[1]+=x[IX['g_pred']]==x[0]; B[2]+=x[IX['g_py']]; B[3]+=x[IX['z_py']]; B[4]+=x[IX['z_pred']]==x[0]
    print(f"== {ds} {sc}: noisy images, rounds 25-50, by share of the TRUE class this client holds")
    for b in sorted(bins):
      n,a,gp,zp,za=bins[b]
      print(f"   share {b*25:>2}-{b*25+25}%: n={n:5d}  global predicts the wrong label {a/n:.2f} (P {gp/n:.2f})   zero-shot predicts it {za/n:.2f} (P {zp/n:.2f})")
