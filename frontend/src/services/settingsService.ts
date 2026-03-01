import { api } from "./api";

export interface AppSettings {
  auto_publish: boolean;
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
