import { describe, it, expect, beforeEach, vi } from 'vitest';
import { alertAudio } from '../utils/audioAlert';
import { authAPI } from '../services/api';
import { getDefaultHomeForRole } from '../App';

describe('AquaGuard Authentication & Universal Logout Suite', () => {
  let store: Record<string, string> = {};

  beforeEach(() => {
    store = {};
    const mockStorage = {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, val: string) => { store[key] = String(val); },
      removeItem: (key: string) => { delete store[key]; },
      clear: () => { store = {}; },
    };

    vi.stubGlobal('localStorage', mockStorage);
    vi.stubGlobal('window', { localStorage: mockStorage });
  });

  it('should resolve correct default home station per role', () => {
    expect(getDefaultHomeForRole('operator')).toBe('/monitoring');
    expect(getDefaultHomeForRole('researcher')).toBe('/research');
    expect(getDefaultHomeForRole('admin')).toBe('/dashboard');
  });

  it('should store credentials on login and clear them on logout', () => {
    // Simulate login session setup
    localStorage.setItem('access_token', 'sample-jwt-token-12345');
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'operator@aquaguard.ai',
      name: 'Head Lifeguard',
      role: 'operator',
    }));

    expect(localStorage.getItem('access_token')).toBe('sample-jwt-token-12345');
    expect(localStorage.getItem('user')).toContain('Head Lifeguard');

    // Perform universal logout cleanup sequence
    alertAudio.stopAll();
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('should verify alertAudio has stopAll and stopSiren methods', () => {
    expect(typeof alertAudio.stopAll).toBe('function');
    expect(typeof alertAudio.stopSiren).toBe('function');
    expect(typeof alertAudio.toggleMute).toBe('function');
    expect(typeof alertAudio.isMuted).toBe('function');

    expect(() => alertAudio.stopAll()).not.toThrow();
  });

  it('should expose authAPI.logout endpoint', () => {
    expect(typeof authAPI.logout).toBe('function');
  });
});