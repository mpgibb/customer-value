import unittest
import numpy as np
from study import CONFIG,generate,discounted_value,aipw_effect,select,mature,fit_models,predict,policy_interval

class CustomerTests(unittest.TestCase):
    def test_discounted_geometric_value(self):
        hazards=np.full((1,12),.1)
        self.assertAlmostEqual(discounted_value(hazards,100,0)[0],sum(100*.9**m for m in range(1,13)))
    def test_zero_and_certain_cancellation(self):
        self.assertEqual(discounted_value(np.ones((1,12)),100)[0],0)
        self.assertAlmostEqual(discounted_value(np.zeros((1,12)),100,0)[0],1200)
    def test_doubly_robust_randomized_expectation(self):
        # Averaging the two equally likely assignments recovers the true effect even with wrong regressions.
        score=aipw_effect(np.array([40.,75.]),np.array([0,1]),np.array([10.,10.]),np.array([20.,20.]))
        self.assertEqual(score.mean(),35)
    def test_budget_and_positive_score_constraint(self):
        cohorts=np.repeat([0,1],10);scores=np.arange(-10,10)
        chosen=select(scores,cohorts,.2,True)
        self.assertEqual(chosen[:10].sum(),0);self.assertEqual(chosen[10:].sum(),2)
        self.assertTrue(np.all(scores[chosen]>0))
    def test_maturity_boundary(self):
        np.testing.assert_array_equal(mature(np.array([23,24,29,30]),42),[True,True,True,False])
    def test_seed_and_null_potential_expectations(self):
        config={**CONFIG,'cohorts':6,'customers_per_cohort':12}
        a,o=generate(config,'no_effect');b,p=generate(config,'no_effect')
        np.testing.assert_array_equal(a['value'],b['value']);np.testing.assert_array_equal(o[:,0],o[:,1])
    def test_randomized_assignment_not_outcome_based(self):
        config={**CONFIG,'cohorts':6,'customers_per_cohort':100}
        a,_=generate(config,'stable');b,_=generate(config,'no_effect')
        np.testing.assert_array_equal(a['assignment'],b['assignment']);np.testing.assert_array_equal(a['x'],b['x'])
    def test_future_and_oracle_values_cannot_change_fitted_predictions(self):
        config={**CONFIG,'cohorts':20,'customers_per_cohort':25,'train_cohorts':4,'validation_end':6,'test_start':19}
        data,oracle=generate(config,'stable');model=fit_models(data,config)
        other={k:v.copy() for k,v in data.items()};future=other['cohort']>=4
        other['value'][future]=-1e8;other['churn6'][future]=1;other['churn_month'][future]=1;other['oracle']=oracle*10000
        changed=fit_models(other,config)
        a=predict(model,data['x'][-20:],config);b=predict(changed,data['x'][-20:],config)
        for x,y in zip(a,b):np.testing.assert_array_equal(x,y)
    def test_cluster_interval_zero_effect(self):
        np.testing.assert_array_equal(policy_interval(np.zeros(60),np.repeat(np.arange(12),5)),[0,0,0])

if __name__=='__main__':unittest.main()
