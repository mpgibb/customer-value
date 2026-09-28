"""Small numerical and provenance helpers for the reproducible study."""
from pathlib import Path
import csv, hashlib, json, platform
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit

def clean(value):
    if isinstance(value, (bool,np.bool_)): return bool(value)
    if isinstance(value, dict): return {str(k): clean(v) for k,v in value.items()}
    if isinstance(value, (list,tuple,np.ndarray)): return [clean(v) for v in value]
    if isinstance(value, (float,np.floating)): return round(float(value),6)
    if isinstance(value, (int,np.integer)): return int(value)
    return value

def write_csv(path, header, rows):
    Path(path).parent.mkdir(exist_ok=True,parents=True)
    with open(path,'w',newline='') as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(header)
        for row in rows:w.writerow([f'{float(x):.6f}' if isinstance(x,(float,np.floating)) else x for x in row])

def save_summary(summary):
    summary['synthetic']=True
    summary['python']=platform.python_version()
    summary['numpy']=np.__version__
    summary['scipy']=scipy.__version__
    summary['source_hashes']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted([Path('study.py'),Path('common.py'),Path('config.json'),Path('PROTOCOL.md'),Path('pyproject.toml'),Path('uv.lock'),*Path('tests').glob('*.py')])}
    summary['data_hashes']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted([*Path('data').glob('*.csv'),*Path('results').glob('*.csv')])}
    Path('results/summary.json').write_text(json.dumps(clean(summary),indent=2,allow_nan=False)+'\n')

def design_fit(x):
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-8]=1
    return np.column_stack([np.ones(len(x)),(x-mean)/scale]),mean,scale

def design(x,mean,scale):return np.column_stack([np.ones(len(x)),(x-mean)/scale])

def ridge_fit(x,y,penalty=10.0):
    z,m,s=design_fit(np.asarray(x));reg=np.eye(z.shape[1])*penalty;reg[0,0]=0
    return (np.linalg.solve(np.einsum("ni,nj->ij",z,z)+reg,np.einsum("ni,n->i",z,y)),m,s)

def ridge_predict(model,x):
    b,m,s=model;return np.einsum("ni,i->n",design(np.asarray(x),m,s),b)

def logistic_fit(x,y,penalty=2.0):
    z,m,s=design_fit(np.asarray(x));y=np.asarray(y)
    def objective(b):
        eta=np.einsum("ni,i->n",z,b)
        loss=np.logaddexp(0,eta).sum()-np.sum(y*eta)+penalty*np.sum(b[1:]**2)/2
        gradient=np.einsum("ni,n->i",z,expit(eta)-y);gradient[1:]+=penalty*b[1:]
        return loss,gradient
    fit=minimize(objective,np.zeros(z.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-12,'gtol':1e-7})
    if not fit.success:raise RuntimeError(fit.message)
    return (fit.x,m,s)

def logistic_predict(model,x):
    b,m,s=model;return expit(np.einsum("ni,i->n",design(np.asarray(x),m,s),b))

def calibration(y,p,bins=5):
    edges=np.linspace(0,1,bins+1);out=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        mask=(p>=lo)&((p<hi) if hi<1 else (p<=hi))
        if mask.any():out.append({'lower':lo,'upper':hi,'n':int(mask.sum()),'predicted':p[mask].mean(),'observed':y[mask].mean()})
    return out

def block_interval(values,rng,draws=1000,block=4):
    values=np.asarray(values);n=len(values)
    indices=(rng.integers(0,n,size=(draws,int(np.ceil(n/block)),1))+np.arange(block))%n
    estimates=values[indices.reshape(draws,-1)[:,:n]].mean(axis=1)
    return [float(values.mean()),*np.quantile(estimates,[.025,.975]).tolist()]
