import * as wmillClient from 'windmill-client';

export const backend: Record<string, (args?: any) => Promise<any>> = new Proxy({}, {
  get: (_target, prop: string) => {
    return async (args: any = {}) => {
      try {
        if ((wmillClient as any).runBackend) {
          return await (wmillClient as any).runBackend(prop, args);
        }
      } catch (e) {
        console.warn(`wmillClient.runBackend for ${prop}:`, e);
      }
      return null;
    };
  }
});

export const backendAsync: Record<string, (args?: any) => Promise<string>> = new Proxy({}, {
  get: (_target, prop: string) => {
    return async (args: any = {}) => {
      if ((wmillClient as any).runBackendAsync) {
        return await (wmillClient as any).runBackendAsync(prop, args);
      }
      return '';
    };
  }
});

export const waitJob = async (jobId: string) => {
  if ((wmillClient as any).waitJob) {
    return await (wmillClient as any).waitJob(jobId);
  }
  return null;
};

export const getJob = async (jobId: string) => {
  if ((wmillClient as any).getJob) {
    return await (wmillClient as any).getJob(jobId);
  }
  return null;
};
