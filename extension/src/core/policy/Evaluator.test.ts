import { describe, it, expect } from 'vitest';
import {
  evaluatePolicies,
  normalizeAction,
  Policy,
  Finding,
} from './Evaluator';

describe('Policy Evaluator Module', () => {
  describe('normalizeAction', () => {
    it('normalizes block actions correctly', () => {
      expect(normalizeAction('block')).toBe('BLOCK');
      expect(normalizeAction('BLOCKED')).toBe('BLOCK');
      expect(normalizeAction('BLOCK')).toBe('BLOCK');
    });

    it('normalizes warn actions correctly', () => {
      expect(normalizeAction('warn')).toBe('WARN');
      expect(normalizeAction('WARNING')).toBe('WARN');
      expect(normalizeAction('WARN')).toBe('WARN');
    });

    it('defaults to ALLOW for other actions', () => {
      expect(normalizeAction('allow')).toBe('ALLOW');
      expect(normalizeAction('ALLOWED')).toBe('ALLOW');
      expect(normalizeAction('unknown')).toBe('ALLOW');
    });
  });

  describe('evaluatePolicies - Default Fallback Thresholds', () => {
    it('returns ALLOW when score is below legacy threshold (<= 80) and no policies matched', () => {
      const result = evaluatePolicies({
        promptText: 'Hello world',
        riskScore: 50,
        policies: [],
      });

      expect(result.action).toBe('ALLOW');
      expect(result.triggeredPolicyName).toBeNull();
      expect(result.triggeredRule).toBeNull();
      expect(result.calculatedRiskScore).toBe(50);
    });

    it('returns BLOCK when score exceeds legacy threshold (> 80) and no policies matched', () => {
      const result = evaluatePolicies({
        promptText: 'Malicious payload',
        riskScore: 85,
        policies: [],
      });

      expect(result.action).toBe('BLOCK');
      expect(result.triggeredPolicyName).toBe('Default Legacy Threshold');
      expect(result.triggeredRule).toBeNull();
      expect(result.calculatedRiskScore).toBe(85);
    });

    it('uses custom max_risk_score from active policy config when no rules match', () => {
      const mockPolicies: Policy[] = [
        {
          name: 'Strict Config Policy',
          is_active: true,
          config: { max_risk_score: 60 },
          rules: [],
        },
      ];

      const resultLow = evaluatePolicies({
        riskScore: 55,
        policies: mockPolicies,
      });
      expect(resultLow.action).toBe('ALLOW');

      const resultHigh = evaluatePolicies({
        riskScore: 65,
        policies: mockPolicies,
      });
      expect(resultHigh.action).toBe('BLOCK');
      expect(resultHigh.triggeredPolicyName).toBe('Default Legacy Threshold');
    });
  });

  describe('evaluatePolicies - Rule Matching Logic', () => {
    it('evaluates semantic rules correctly against risk score', () => {
      const mockPolicies: Policy[] = [
        {
          name: 'Semantic Risk Policy',
          is_active: true,
          rules: [
            {
              condition_type: 'semantic',
              condition_value: '> 70',
              action: 'BLOCK',
              priority: 1,
              is_active: true,
            },
          ],
        },
      ];

      const result = evaluatePolicies({
        riskScore: 75,
        policies: mockPolicies,
      });

      expect(result.action).toBe('BLOCK');
      expect(result.triggeredPolicyName).toBe('Semantic Risk Policy');
      expect(result.triggeredRule?.condition_value).toBe('> 70');
    });

    it('evaluates regex rules against prompt text', () => {
      const mockPolicies: Policy[] = [
        {
          name: 'API Key Protection',
          is_active: true,
          rules: [
            {
              condition_type: 'regex',
              condition_value: 'sk-[a-zA-Z0-9]{10,}',
              action: 'BLOCK',
              priority: 1,
              is_active: true,
            },
          ],
        },
      ];

      const result = evaluatePolicies({
        promptText: 'My key is sk-abc123xyz9876543',
        policies: mockPolicies,
      });

      expect(result.action).toBe('BLOCK');
      expect(result.triggeredPolicyName).toBe('API Key Protection');
    });

    it('evaluates heuristic rules against prompt text keywords (case-insensitive)', () => {
      const mockPolicies: Policy[] = [
        {
          name: 'Confidentiality Policy',
          is_active: true,
          rules: [
            {
              condition_type: 'heuristic',
              condition_value: 'CONFIDENTIAL',
              action: 'WARN',
              priority: 5,
              is_active: true,
            },
          ],
        },
      ];

      const result = evaluatePolicies({
        promptText: 'This document contains confidential information.',
        policies: mockPolicies,
      });

      expect(result.action).toBe('WARN');
      expect(result.triggeredPolicyName).toBe('Confidentiality Policy');
    });

    it('respects rule priority (lower priority evaluated first)', () => {
      const mockPolicies: Policy[] = [
        {
          name: 'Priority Policy',
          is_active: true,
          rules: [
            {
              id: 'rule-low-priority',
              condition_type: 'heuristic',
              condition_value: 'password',
              action: 'BLOCK',
              priority: 20,
              is_active: true,
            },
            {
              id: 'rule-high-priority',
              condition_type: 'heuristic',
              condition_value: 'password',
              action: 'WARN',
              priority: 5,
              is_active: true,
            },
          ],
        },
      ];

      const result = evaluatePolicies({
        promptText: 'Please enter your password',
        policies: mockPolicies,
      });

      expect(result.action).toBe('WARN');
      expect(result.triggeredRule?.id).toBe('rule-high-priority');
    });

    it('ignores inactive policies and inactive rules', () => {
      const mockPolicies: Policy[] = [
        {
          name: 'Disabled Policy',
          is_active: false,
          rules: [
            {
              condition_type: 'heuristic',
              condition_value: 'secret',
              action: 'BLOCK',
              priority: 1,
              is_active: true,
            },
          ],
        },
        {
          name: 'Active Policy with Disabled Rule',
          is_active: true,
          rules: [
            {
              condition_type: 'heuristic',
              condition_value: 'secret',
              action: 'BLOCK',
              priority: 1,
              is_active: false,
            },
          ],
        },
      ];

      const result = evaluatePolicies({
        promptText: 'This is a secret',
        policies: mockPolicies,
      });

      expect(result.action).toBe('ALLOW');
      expect(result.triggeredPolicyName).toBeNull();
    });
  });

  describe('evaluatePolicies - Normalized Findings Input', () => {
    it('accepts an array of normalized findings directly and derives risk score', () => {
      const findings: Finding[] = [
        {
          type: 'data_leak',
          score: 82,
          label: 'API Key',
          snippet: 'sk-proj1234567890',
        },
        {
          type: 'pii',
          score: 40,
          label: 'Email',
          snippet: 'user@example.com',
        },
      ];

      const mockPolicies: Policy[] = [
        {
          name: 'Detector Findings Policy',
          is_active: true,
          rules: [
            {
              condition_type: 'semantic',
              condition_value: '>= 80',
              action: 'BLOCK',
              priority: 10,
              is_active: true,
            },
          ],
        },
      ];

      const result = evaluatePolicies(findings, mockPolicies);

      expect(result.calculatedRiskScore).toBe(82);
      expect(result.action).toBe('BLOCK');
      expect(result.triggeredPolicyName).toBe('Detector Findings Policy');
    });

    it('matches heuristic/regex against finding snippets when promptText is omitted', () => {
      const findings: Finding[] = [
        {
          type: 'heuristic_match',
          snippet: 'INTERNAL USE ONLY - project launch details',
        },
      ];

      const mockPolicies: Policy[] = [
        {
          name: 'Internal Material Policy',
          is_active: true,
          rules: [
            {
              condition_type: 'heuristic',
              condition_value: 'internal use only',
              action: 'WARN',
              priority: 1,
              is_active: true,
            },
          ],
        },
      ];

      const result = evaluatePolicies(findings, mockPolicies);

      expect(result.action).toBe('WARN');
      expect(result.triggeredPolicyName).toBe('Internal Material Policy');
    });
  });
});
