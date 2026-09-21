// AquaGuard AI - Native Browser Push Notification Dispatcher (Phase 11)
// Provides desktop push notifications for on-duty lifeguards and operators,
// ensuring immediate visual interruption even when the browser is minimized or tab is in background.

export interface PushNotificationOptions {
  body: string;
  tag?: string;
  requireInteraction?: boolean;
  data?: Record<string, unknown>;
  icon?: string;
}

class BrowserNotificationManager {
  private enabled: boolean;

  constructor() {
    const savedPref = localStorage.getItem('aquaguard_push_notifications_enabled');
    // Default to true if not explicitly disabled
    this.enabled = savedPref === null ? true : savedPref === 'true';
  }

  public isSupported(): boolean {
    return typeof window !== 'undefined' && 'Notification' in window;
  }

  public getPermission(): NotificationPermission {
    if (!this.isSupported()) return 'denied';
    return Notification.permission;
  }

  public isEnabled(): boolean {
    return this.isSupported() && this.enabled && Notification.permission === 'granted';
  }

  public async requestPermission(): Promise<boolean> {
    if (!this.isSupported()) return false;
    try {
      const perm = await Notification.requestPermission();
      if (perm === 'granted') {
        this.setEnabled(true);
        return true;
      } else {
        this.setEnabled(false);
        return false;
      }
    } catch {
      return false;
    }
  }

  public setEnabled(val: boolean) {
    this.enabled = val;
    localStorage.setItem('aquaguard_push_notifications_enabled', String(val));
  }

  public sendEmergencyAlert(
    title: string,
    body: string,
    options?: Partial<PushNotificationOptions>
  ): boolean {
    if (!this.isEnabled()) return false;

    try {
      const notification = new Notification(title, {
        body,
        icon: '/favicon.ico',
        tag: options?.tag || 'aquaguard-emergency',
        requireInteraction: options?.requireInteraction ?? true,
        data: options?.data,
      });

      notification.onclick = () => {
        window.focus();
        if (window.location.pathname !== '/alerts') {
          window.location.href = '/alerts';
        }
        notification.close();
      };

      return true;
    } catch (e) {
      console.warn('[BrowserNotification] Failed to display notification:', e);
      return false;
    }
  }

  public async testNotification(): Promise<{ success: boolean; message: string }> {
    if (!this.isSupported()) {
      return { success: false, message: 'Browser notifications are not supported in this browser.' };
    }

    if (Notification.permission !== 'granted') {
      const granted = await this.requestPermission();
      if (!granted) {
        return {
          success: false,
          message: 'Notification permission denied. Please allow notifications in your browser settings.',
        };
      }
    }

    const dispatched = this.sendEmergencyAlert(
      '🚨 [TEST DRILL] AquaGuard AI Emergency System',
      'This is a verified test broadcast. Desktop emergency push notifications are active.',
      { tag: 'test-drill', requireInteraction: false }
    );

    if (dispatched) {
      return { success: true, message: 'Desktop notification sent successfully!' };
    }
    return { success: false, message: 'Could not display desktop notification.' };
  }
}

export const browserNotification = new BrowserNotificationManager();
