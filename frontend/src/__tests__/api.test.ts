import { describe, it, expect } from 'vitest';
import api, { authAPI, systemAPI, alertAPI, experimentAPI } from '../services/api';

describe('AquaGuard Frontend API Client', () => {
  it('should initialize Axios with correct default timeout and headers', () => {
    expect(api.defaults.timeout).toBe(30000);
    expect(api.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('should expose all required authentication API endpoints', () => {
    expect(typeof authAPI.login).toBe('function');
    expect(typeof authAPI.logout).toBe('function');
  });

  it('should expose all required system and edge optimization endpoints', () => {
    expect(typeof systemAPI.health).toBe('function');
    expect(typeof systemAPI.getStatus).toBe('function');
    expect(typeof systemAPI.getEdgeStatus).toBe('function');
    expect(typeof systemAPI.configureEdge).toBe('function');
    expect(typeof systemAPI.runBenchmark).toBe('function');
    expect(typeof systemAPI.exportModels).toBe('function');
  });

  it('should expose emergency dispatch and alert endpoints', () => {
    expect(typeof alertAPI.list).toBe('function');
    expect(typeof alertAPI.acknowledge).toBe('function');
    expect(typeof alertAPI.resolve).toBe('function');
    expect(typeof alertAPI.getChannels).toBe('function');
    expect(typeof alertAPI.testDispatch).toBe('function');
    expect(typeof alertAPI.dispatchAlert).toBe('function');
  });

  it('should expose research benchmark endpoints', () => {
    expect(typeof experimentAPI.list).toBe('function');
    expect(typeof experimentAPI.getComparison).toBe('function');
  });
});
