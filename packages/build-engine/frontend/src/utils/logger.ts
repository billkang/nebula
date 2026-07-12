const API_BASE = '/api/v1';

type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  stack: string | null;
}

class Logger {
  private queue: LogEntry[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;
  private readonly BATCH_SIZE = 10;
  private readonly FLUSH_INTERVAL = 5000; // 5 seconds
  private readonly ENDPOINT = `${API_BASE}/logs`;

  constructor() {
    // Set up periodic flush
    this.timer = setInterval(() => this.flush(), this.FLUSH_INTERVAL);

    // Flush on page close via sendBeacon
    if (typeof window !== 'undefined' && 'navigator' in window) {
      window.addEventListener('beforeunload', () => this.flushSync());
    }
  }

  private enqueue(level: LogLevel, message: string, error?: Error | unknown): void {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      stack: null,
    };

    if (error instanceof Error) {
      entry.stack = error.stack ?? null;
      entry.message = `${message}: ${error.message}`;
    } else if (error) {
      entry.message = `${message}: ${String(error)}`;
    }

    this.queue.push(entry);

    // Flush immediately if batch size reached
    if (this.queue.length >= this.BATCH_SIZE) {
      this.flush();
    }
  }

  debug(message: string, error?: unknown): void {
    console.debug(`[Nebula] ${message}`, error ?? '');
    this.enqueue('debug', message, error);
  }

  info(message: string, error?: unknown): void {
    console.info(`[Nebula] ${message}`, error ?? '');
    this.enqueue('info', message, error);
  }

  warn(message: string, error?: unknown): void {
    console.warn(`[Nebula] ${message}`, error ?? '');
    this.enqueue('warning', message, error);
  }

  error(message: string, error?: unknown): void {
    console.error(`[Nebula] ${message}`, error ?? '');
    this.enqueue('error', message, error);
  }

  private async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0);
    try {
      const token = localStorage.getItem('nebula_token');
      const response = await fetch(this.ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(batch),
      });
      if (!response.ok) {
        console.warn(`[Nebula] Log upload failed: ${response.status}`);
        // Re-queue on failure (add back to front of queue)
        this.queue.unshift(...batch);
      }
    } catch (err) {
      // Silent degradation — don't throw, don't alert
      console.debug('[Nebula] Log upload failed (backend unreachable):', err);
      // Re-queue for retry
      this.queue.unshift(...batch);
    }
  }

  private flushSync(): void {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0);

    try {
      const token = localStorage.getItem('nebula_token');
      const blob = new Blob([JSON.stringify(batch)], { type: 'application/json' });
      navigator.sendBeacon(this.ENDPOINT, blob);
    } catch {
      // Silent degradation on page close
    }
  }

  /** Cleanup — call when unmounting (e.g., in tests) */
  destroy(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

export const logger = new Logger();
