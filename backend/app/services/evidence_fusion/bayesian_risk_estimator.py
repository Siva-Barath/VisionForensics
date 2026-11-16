"""
Bayesian Risk Estimator.
Calculates posterior risk deterministically and builds a Decision Trace.
"""
from typing import Dict, Tuple
from .models import DecisionTrace, DecisionTraceStep, RiskBreakdown, EvidenceContribution

class BayesianRiskEstimator:
    def estimate(
        self, 
        normalized_evidence: Dict[str, float], 
        effective_weights: Dict[str, float], 
        correlation_multiplier: float, 
        calibrated_confidence: float
    ) -> Tuple[float, RiskBreakdown, DecisionTrace]:
        
        prior = 0.05
        current_posterior = prior
        
        trace = DecisionTrace()
        trace.steps.append(DecisionTraceStep(
            stage="Initialization", 
            description="Setting base prior risk", 
            value_change="0%", 
            current_posterior=current_posterior
        ))
        
        contributors = []
        
        # We step through each evidence category and apply a Naive Bayes-like update
        # P(Forgery | E) = P(E | Forgery) * P(Forgery) / P(E)
        # For a deterministic, bounded, explainable approach, we use Odds form or an additive bounded function.
        # Let's use a logistic/odds approach shifted by the evidence
        
        # Convert to odds
        def to_odds(p): return p / (1 - p + 1e-9)
        def to_prob(o): return o / (1 + o)
        
        current_odds = to_odds(prior)
        
        for cat, val in normalized_evidence.items():
            weight = effective_weights.get(cat, 0.0)
            
            # If val is 0.5, it's neutral. > 0.5 points to forgery.
            # Shift = (val - 0.5) * 2.0  -> ranges [-1.0, 1.0]
            # Multiply by weight
            shift = (val - 0.5) * 2.0 * weight * correlation_multiplier * 5.0 # arbitrary scaling factor for odds
            
            # Apply shift multiplicatively to odds (like a likelihood ratio)
            likelihood_ratio = 10 ** shift
            
            old_post = to_prob(current_odds)
            current_odds *= likelihood_ratio
            new_post = to_prob(current_odds)
            
            risk_shift = new_post - old_post
            
            if abs(risk_shift) > 0.001:
                contributors.append(EvidenceContribution(
                    category=cat, 
                    base_weight=weight, 
                    effective_weight=weight * calibrated_confidence, 
                    risk_shift=risk_shift
                ))
                
                trace.steps.append(DecisionTraceStep(
                    stage=cat,
                    description=f"Applied normalized evidence {val:.2f} with weight {weight:.2f}",
                    value_change=f"{risk_shift * 100:+.1f}%",
                    current_posterior=new_post
                ))
                
        # Finally, apply global calibrated confidence penalty if necessary
        # We shrink the posterior towards the prior if confidence is low
        final_post = prior + (to_prob(current_odds) - prior) * calibrated_confidence
        final_shift = final_post - to_prob(current_odds)
        
        if abs(final_shift) > 0.001:
            trace.steps.append(DecisionTraceStep(
                stage="Confidence Calibration",
                description=f"Applied global confidence multiplier {calibrated_confidence:.2f}",
                value_change=f"{final_shift * 100:+.1f}%",
                current_posterior=final_post
            ))
            
        breakdown = RiskBreakdown(
            prior_risk=prior,
            posterior_risk=final_post,
            contributors=contributors
        )
        
        return final_post, breakdown, trace
