import { api } from "./api";

export interface SocialAccount {
  id: string;
  platform: string;
  channel_id: string | null;
  channel_title: string | null;
  created_at: string | null;
}

export interface SocialAccountsListResponse {
  accounts: SocialAccount[];
}

export const socialService = {
  async getAccounts(): Promise<SocialAccount[]> {
    const response = await api.get<SocialAccountsListResponse>("/social/accounts");
    return response.data.accounts;
  },

  async connectPlatform(platform: string): Promise<string> {
    const response = await api.get<{ auth_url: string }>(`/social/connect/${platform}`);
    return response.data.auth_url;
  },

  async disconnectAccount(accountId: string): Promise<void> {
    await api.delete(`/social/accounts/${accountId}`);
  },
};
