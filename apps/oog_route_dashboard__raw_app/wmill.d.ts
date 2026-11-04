declare module './wmill' {
  export const backend: {
    calculate_route: (args: {
      origin_query?: string;
      destination_query?: string;
      cargo_weight_mt?: number;
      cargo_height_m?: number;
      cargo_width_m?: number;
      cargo_length_m?: number;
      axle_count?: number;
      allow_bypasses?: boolean;
      client_id?: string;
    }) => Promise<any>;
    get_preset_scenarios: () => Promise<any[]>;
    record_dispatcher_override: (args: {
      survey_id: string;
      dispatcher_name: string;
      engineering_waiver_reason: string;
      current_risk_score?: number;
    }) => Promise<any>;
    [key: string]: (args?: any) => Promise<any>;
  };
  export const backendAsync: Record<string, (args?: any) => Promise<string>>;
  export const waitJob: (jobId: string) => Promise<any>;
  export const getJob: (jobId: string) => Promise<any>;
}
