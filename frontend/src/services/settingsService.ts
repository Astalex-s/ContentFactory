import { api } from "./api";

export interface AppSettings {
  auto_publish: boolean;
  publish_rate_limit_enabled: boolean;
}

export const settingsService = {
  async getSettings(): Promise<AppSettings> {
    const { data } = await api.get<AppSettings>("/settings");
    return data;
  },

  async updateSettings(updates: Partial<AppSettings>): Promise<AppSettings> {
    const { data } = await api.patch<AppSettings>("/settings", updates);
    return data;
  },
};
