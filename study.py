"""Temporal churn/value prediction and honest randomized policy evaluation."""
from pathlib import Path
import json
import numpy as np
from scipy.special import expit
from scipy.stats import t as student_t
from common import write_csv,save_summary,ridge_fit,ridge_predict,logistic_fit,logistic_predict,calibration

CONFIG=json.loads(Path('config.json').read_text())

def features(x):
    tenure,e,f,tier,margin=x.T
    return np.column_stack([np.log1p(tenure),e,f,tier,margin,e*e,f*f,e*f,e*tier,e*margin,f*margin])

def discounted_value(hazards,margin,annual_rate=.1):
    survival=np.cumprod(1-np.asarray(hazards),axis=-1)
    discounts=(1+annual_rate)**(np.arange(1,survival.shape[-1]+1)/12)
    return (survival*np.asarray(margin)/discounts).sum(axis=-1)

def generate(config,scenario):
    rng=np.random.default_rng(config['seed']);n=config['cohorts']*config['customers_per_cohort'];months=np.arange(1,13)
    cohort=np.repeat(np.arange(config['cohorts']),config['customers_per_cohort'])
    tenure=rng.uniform(1,48,n);engagement=rng.beta(2,2,n);friction=rng.normal(0,1,n);tier=rng.integers(0,2,n)
    margin=np.round(18+25*tier+20*engagement+rng.lognormal(2,.4,n),6)
    x=np.column_stack([tenure,engagement,friction,tier,margin]);assignment=rng.integers(0,2,n)
    base=-3.1+2.4*(.5-engagement)+.65*friction+.2*tier-.12*np.log1p(tenure)
    delta=.6-1.7*engagement+.2*friction
    if scenario=='no_effect':delta[:]=0
    if scenario=='response_shift':delta[cohort>=config['test_start']]*=-1.8
    h0=expit(base[:,None]+.03*months);h1=expit(base[:,None]+.03*months+delta[:,None])
    uniforms=rng.random((n,12));noise=rng.normal(0,3,(n,12))
    margins=margin[:,None]*(1+.005*months)+noise
    survival0=np.cumprod(uniforms>=h0,axis=1);survival1=np.cumprod(uniforms>=h1,axis=1)
    survival=np.where(assignment[:,None]==1,survival1,survival0)
    observed_margin=survival*margins
    discounts=(1+config['annual_discount_rate'])**(months/12)
    value=(observed_margin/discounts).sum(axis=1)
    churn=1-survival[:,5]
    churn_month=np.where(survival[:,-1]==0,np.argmin(survival,axis=1)+1,13)
    expected_margin=margin[:,None]*(1+.005*months)
    oracle=np.column_stack([discounted_value(h0,expected_margin,config['annual_discount_rate']),discounted_value(h1,expected_margin,config['annual_discount_rate'])])
    return {'id':np.arange(n),'cohort':cohort,'x':x,'assignment':assignment,'value':value,'churn6':churn,'churn_month':churn_month,'survival':survival,'monthly_margin':observed_margin},oracle

def mature(cohort,cutoff,horizon=12):return np.asarray(cohort)+horizon<cutoff

def fit_models(data,config):
    # Fitting accepts observed data only. Potential expectations have no path here.
    train=data['cohort']<config['train_cohorts'];assert np.all(mature(data['cohort'][train],config['test_start']))
    x=features(data['x']);a=data['assignment'];y=data['value'];control=train&(a==0)
    hazard_x=[];hazard_y=[]
    for i in np.where(control)[0]:
        for month in range(1,min(12,int(data['churn_month'][i]))+1):
            hazard_x.append(np.r_[x[i],month]);hazard_y.append(int(data['churn_month'][i]==month))
    hazard=logistic_fit(np.asarray(hazard_x),np.asarray(hazard_y))
    nuisance=[ridge_fit(x[train&(a==arm)],y[train&(a==arm)],30) for arm in [0,1]]
    # Fold assignment is independent of treatment/outcome; every training prediction is out of fold.
    folds=np.random.default_rng(config['seed']+8).permutation(np.where(train)[0]);fold_id=np.full(len(x),-1)
    for fold,ids in enumerate(np.array_split(folds,3)):fold_id[ids]=fold
    scores=np.zeros(len(x))
    for fold in range(3):
        fit=train&(fold_id!=fold);held=train&(fold_id==fold)
        m=[ridge_fit(x[fit&(a==arm)],y[fit&(a==arm)],30) for arm in [0,1]]
        m0=ridge_predict(m[0],x[held]);m1=ridge_predict(m[1],x[held])
        scores[held]=aipw_effect(y[held],a[held],m0,m1)
    learner=ridge_fit(x[train],scores[train],80)
    baseline={}
    for tier in [0,1]:
        mask=control&(data['x'][:,3]==tier)
        baseline[tier]={'churn':data['churn6'][mask].mean(),'value':y[mask].mean()}
    return {'hazard':hazard,'nuisance':nuisance,'learner':learner,'baseline':baseline}

def aipw_effect(y,a,m0,m1):return m1-m0+2*a*(y-m1)-2*(1-a)*(y-m0)

def predict(models,x,config):
    basis=features(x)
    hazards=np.column_stack([logistic_predict(models['hazard'],np.column_stack([basis,np.full(len(x),month)])) for month in range(1,13)])
    return 1-np.prod(1-hazards[:,:6],axis=1),discounted_value(hazards,x[:,4,None],config['annual_discount_rate']),ridge_predict(models['learner'],basis)

def select(scores,cohorts,fraction,positive=False):
    selected=np.zeros(len(scores),bool)
    for cohort in np.unique(cohorts):
        indices=np.flatnonzero(cohorts==cohort);k=int(np.floor(len(indices)*fraction))
        ordered=indices[np.argsort(-scores[indices],kind='stable')][:k]
        if positive:ordered=ordered[scores[ordered]>0]
        selected[ordered]=True
    return selected

def policy_interval(values,cohorts):
    means=np.array([values[cohorts==c].mean() for c in np.unique(cohorts)])
    estimate=values.mean();se=means.std(ddof=1)/np.sqrt(len(means));q=student_t.ppf(.975,len(means)-1)
    return [estimate,estimate-q*se,estimate+q*se]

def evaluate(config,scenario):
    data,oracle=generate(config,scenario);models=fit_models(data,config)
    rows=np.column_stack([data['id'],data['cohort'],data['x'],data['assignment'],data['churn6'],data['churn_month'],data['value']])
    write_csv(f'data/{scenario}_customers.csv',['customer_id','cohort','tenure_months','engagement','friction','tier','monthly_margin','assigned','churn6','churn_month','discounted_contribution'],rows)
    write_csv(f'data/{scenario}_oracle.csv',['customer_id','expected_control','expected_treatment'],np.column_stack([data['id'],oracle]))
    months=[]
    for i in range(len(data['id'])):
        for month in range(12):
            if month==0 or data['survival'][i,month-1]:months.append([i,int(data['cohort'][i]+month+1),month+1,int(1-data['survival'][i,month]),data['monthly_margin'][i,month]])
    write_csv(f'data/{scenario}_monthly.csv',['customer_id','outcome_cohort','month','cancelled','contribution'],months)
    test=data['cohort']>=config['test_start'];ids=np.flatnonzero(test);x=data['x'][test];cohorts=data['cohort'][test];a=data['assignment'][test];y=data['value'][test]
    risk,value,effect=predict(models,x,config);cost=config['treatment_cost']
    policies={'none':np.zeros(len(ids),bool),'all':np.ones(len(ids),bool),'high_risk':select(risk,cohorts,config['budget_fraction']),'high_value':select(value,cohorts,config['budget_fraction']),'incremental_value':select(effect-cost,cohorts,config['budget_fraction'],True)}
    true_effect=oracle[test,1]-oracle[test,0]
    oracle_selected=select(true_effect-cost,cohorts,config['budget_fraction'],True)
    oracle_gain=np.mean(oracle_selected*(true_effect-cost))
    m0=ridge_predict(models['nuisance'][0],features(x));m1=ridge_predict(models['nuisance'][1],features(x))
    score=aipw_effect(y,a,m0,m1)
    results={}
    for name,selection in policies.items():
        estimate,lo,hi=policy_interval(selection*(score-cost),cohorts)
        gain=np.mean(selection*(true_effect-cost))
        results[name]={'target_rate':selection.mean(),'incremental_net_per_customer':estimate,'lower95':lo,'upper95':hi,'oracle_expected_net':gain,'regret_to_budget_oracle':oracle_gain-gain if name!='all' else None,'accounting_cost_sensitivity':{str(c):float(np.mean(selection*(score-c))) for c in [15,35,55]}}
    controls=a==0;target=data['churn6'][test][controls];actual=y[controls]
    br=np.array([models['baseline'][int(t)]['churn'] for t in x[:,3]])[controls]
    bv=np.array([models['baseline'][int(t)]['value'] for t in x[:,3]])[controls]
    prediction={}
    for name,p,v in [('segment_mean',br,bv),('survival',risk[controls],value[controls])]:
        prediction[name]={'brier':np.mean((p-target)**2),'log_loss':-np.mean(target*np.log(np.clip(p,1e-9,1))+(1-target)*np.log(np.clip(1-p,1e-9,1))),'value_mae':np.abs(actual-v).mean(),'value_bias':(v-actual).mean(),'calibration':calibration(target,p)}
    validation=(data['cohort']>=config['train_cohorts'])&(data['cohort']<config['validation_end'])&(data['assignment']==0)
    assert np.all(mature(data['cohort'][validation],config['test_start']))
    vr,vv,_=predict(models,data['x'][validation],config)
    validation_metrics={'customers':int(validation.sum()),'brier':np.mean((vr-data['churn6'][validation])**2),'value_mae':np.abs(vv-data['value'][validation]).mean()}
    result_rows=np.column_stack([ids,cohorts,a,y,risk,value,effect,score,*policies.values(),true_effect])
    write_csv(f'results/{scenario}_scored_customers.csv',['customer_id','cohort','assignment','contribution','churn_prediction','value_prediction','gross_effect_prediction','aipw_gross_effect',*policies.keys(),'oracle_expected_effect'],result_rows)
    return {'scenario':scenario,'customers':len(data['id']),'test_customers':len(ids),'test_controls':int(controls.sum()),'cohort_clusters':len(np.unique(cohorts)),'prediction':prediction,'validation':validation_metrics,'policies':results,'budget_oracle_net':oracle_gain}

def main():
    summary={'study':'customer-value','config':CONFIG,'scenarios':[evaluate(CONFIG,s) for s in CONFIG['scenarios']]};save_summary(summary)
    print(json.dumps({s['scenario']:{'prediction':s['prediction'],'policies':s['policies']} for s in summary['scenarios']},default=float,indent=2))

if __name__=='__main__':main()
