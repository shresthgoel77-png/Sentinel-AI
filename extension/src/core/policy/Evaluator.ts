/**
 * Standalone TypeScript Policy Evaluator for Extension.
 * Re-implements risk scoring and threshold enforcement logic from backend/policy_engine.py.
 */

export type PolicyAction = 'ALLOW' | 'WARN' | 'BLOCK';

export interface PolicyRule {
  id?: number | string;
  policy_id?: number | string;
  condition_type: 'semantic' | 'regex' | 'heuristic' | string;
  condition_value: string;
  action: 'ALLOW' | 'WARN' | 'BLOCK' | 'allow' | 'warn' | 'block' | 'ALLOWED' | 'BLOCKED' | string;
  priority: number;
  is_active: boolean;
}

export interface PolicyConfig {
  max_risk_score?: number;
  enable_masking?: boolean;
  [key: string]: any;
}

export interface Policy {
  id?: number | string;
  name: string;
  description?: string;
  tenant_id?: number | string;
  type?: string;
  is_active: boolean;
  config?: PolicyConfig | null;
  scope?: string;
  created_at?: string | Date;
  rules: PolicyRule[];
}

export interface Finding {
  type?: string;
  score?: number;
  risk_score?: number;
  label?: string;
  snippet?: string;
  text?: string;
  metadata?: Record<string, any>;
}

export interface EvaluationOptions {
  promptText?: string;
  riskScore?: number;
  findings?: Finding[];
  policies?: Policy[];
  tenantId?: number | string;
}

export interface EvaluationResult {
  action: PolicyAction;
  triggeredPolicyName: string | null;
  triggeredRule: PolicyRule | null;
  calculatedRiskScore: number;
}

/**
 * Normalizes action string into standard PolicyAction union ('ALLOW' | 'WARN' | 'BLOCK')
 */
export function normalizeAction(actionStr: string): PolicyAction {
  const normalized = actionStr.trim().toUpperCase();
  if (normalized === 'BLOCK' || normalized === 'BLOCKED') {
    return 'BLOCK';
  }
  if (normalized === 'WARN' || normalized === 'WARNING') {
    return 'WARN';
  }
  return 'ALLOW';
}

/**
 * Parses numeric threshold from condition value (e.g. "> 80", ">= 80", "80")
 */
function parseThreshold(conditionValue: string): number | null {
  const cleaned = conditionValue.replace(/[>=]/g, '').trim();
  const parsed = parseFloat(cleaned);
  return isNaN(parsed) ? null : parsed;
}

/**
 * Evaluates dynamic rules against findings, prompt text, and risk score.
 * Mirrors backend/policy_engine.py evaluate_policies.
 *
 * @param input Evaluation options object OR array of normalized findings
 * @param mockPolicies Optional array of local mock policies when findings array is passed directly
 */
export function evaluatePolicies(
  input: EvaluationOptions | Finding[],
  mockPolicies?: Policy[]
): EvaluationResult {
  let promptText = '';
  let explicitRiskScore: number | undefined = undefined;
  let findings: Finding[] = [];
  let policies: Policy[] = mockPolicies || [];

  if (Array.isArray(input)) {
    findings = input;
  } else {
    promptText = input.promptText || '';
    explicitRiskScore = input.riskScore;
    findings = input.findings || [];
    if (input.policies && input.policies.length > 0) {
      policies = input.policies;
    }
  }

  // Extract risk score: take max of explicit risk score and any finding scores
  const scores: number[] = [];
  if (explicitRiskScore !== undefined) {
    scores.push(explicitRiskScore);
  }
  for (const finding of findings) {
    if (typeof finding.risk_score === 'number') {
      scores.push(finding.risk_score);
    }
    if (typeof finding.score === 'number') {
      scores.push(finding.score);
    }
  }
  const calculatedRiskScore = scores.length > 0 ? Math.max(...scores) : 0;

  // Extract combined prompt text from findings if not explicitly provided
  if (!promptText && findings.length > 0) {
    promptText = findings
      .map((f) => f.text || f.snippet || f.label || '')
      .filter(Boolean)
      .join(' ');
  }

  const activePolicies = policies.filter((p) => p.is_active !== false);

  if (activePolicies.length > 0) {
    for (const policy of activePolicies) {
      // Sort rules by priority ascending
      const sortedRules = [...(policy.rules || [])]
        .filter((r) => r.is_active !== false)
        .sort((a, b) => (a.priority ?? 10) - (b.priority ?? 10));

      for (const rule of sortedRules) {
        let matched = false;

        if (rule.condition_type === 'semantic') {
          const threshold = parseThreshold(rule.condition_value);
          if (threshold !== null && calculatedRiskScore >= threshold) {
            matched = true;
          }
        } else if (rule.condition_type === 'regex') {
          try {
            const re = new RegExp(rule.condition_value, 'i');
            if (re.test(promptText)) {
              matched = true;
            } else if (findings.some((f) => f.snippet && re.test(f.snippet))) {
              matched = true;
            }
          } catch {
            // Ignore invalid regex patterns
          }
        } else if (rule.condition_type === 'heuristic') {
          const target = rule.condition_value.toLowerCase();
          if (promptText.toLowerCase().includes(target)) {
            matched = true;
          } else if (
            findings.some(
              (f) =>
                (f.label && f.label.toLowerCase().includes(target)) ||
                (f.snippet && f.snippet.toLowerCase().includes(target))
            )
          ) {
            matched = true;
          }
        }

        if (matched) {
          const action = normalizeAction(rule.action);
          return {
            action,
            triggeredPolicyName: policy.name,
            triggeredRule: rule,
            calculatedRiskScore,
          };
        }
      }
    }
  }

  // Determine fallback max_risk_score threshold
  let maxRiskThreshold = 80;
  for (const policy of activePolicies) {
    if (policy.config && typeof policy.config.max_risk_score === 'number') {
      maxRiskThreshold = policy.config.max_risk_score;
      break;
    }
  }

  if (calculatedRiskScore > maxRiskThreshold) {
    return {
      action: 'BLOCK',
      triggeredPolicyName: 'Default Legacy Threshold',
      triggeredRule: null,
      calculatedRiskScore,
    };
  }

  return {
    action: 'ALLOW',
    triggeredPolicyName: null,
    triggeredRule: null,
    calculatedRiskScore,
  };
}
