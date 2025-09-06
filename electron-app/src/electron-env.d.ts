declare global {
  interface Window {
    apiClient: {
      request(
        method: string,
        p: string,
        opts?: {
          headers?: Record<string, string>;
          query?: Record<string, unknown>;
          body?: unknown;
        },
      ): Promise<{
        status: number;
        headers: Record<string, string>;
        body: string;
      }>;
      get(
        p: string,
        opts?: {
          headers?: Record<string, string>;
          query?: Record<string, unknown>;
        },
      ): Promise<{
        status: number;
        headers: Record<string, string>;
        body: string;
      }>;
      post(
        p: string,
        body?: unknown,
        opts?: {
          headers?: Record<string, string>;
          query?: Record<string, unknown>;
        },
      ): Promise<{
        status: number;
        headers: Record<string, string>;
        body: string;
      }>;
      put(
        p: string,
        body?: unknown,
        opts?: {
          headers?: Record<string, string>;
          query?: Record<string, unknown>;
        },
      ): Promise<{
        status: number;
        headers: Record<string, string>;
        body: string;
      }>;
      delete(
        p: string,
        opts?: {
          headers?: Record<string, string>;
          query?: Record<string, unknown>;
        },
      ): Promise<{
        status: number;
        headers: Record<string, string>;
        body: string;
      }>;
    };
    electron: {
      ipcRenderer: {
        invoke(channel: string, ...args: unknown[]): Promise<unknown>;
      };
    };
  }
}

export {};
