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

export interface OAuthApp {
  id: string;
  user_id: string | null;
  platform: string;
  name: string;
  client_id_masked: string;
  redirect_uri: string | null;
  created_at: string;
  updated_at: string;
}

export interface OAuthAppListResponse {
  apps: OAuthApp[];
}

export interface OAuthAppCreate {
  platform: string;
  name: string;
  client_id: string;
  client_secret: string;
  redirect_uri?: string;
}

export interface OAuthAppUpdate {
  name?: string;
  client_id?: string;
  client_secret?: string;
  redirect_uri?: string | null;
}

export const socialService = {
  async getAccounts(): Promise<SocialAccount[]> {
    const response = await api.get<SocialAccountsListResponse>("/social/accounts");
    const accounts = response.data?.accounts ?? [];
    return Array.isArray(accounts)
      ? accounts.filter((a) => a && typeof a.id === "string" && a.id.length > 0)
      : [];
  },

  async connectPlatform(platform: string, oauthAppId: string): Promise<string> {
    const response = await api.get<{ auth_url: string }>(`/social/connect/${platform}?oauth_app_id=${oauthAppId}`);
    return response.data.auth_url;
  },

  async updateAccount(accountId: string, data: { channel_title?: string | null }): Promise<SocialAccount> {
    const response = await api.patch<SocialAccount>(`/social/accounts/${accountId}`, data);
    return response.data;
  },

  async disconnectAccount(accountId: string): Promise<void> {
    await api.delete(`/social/accounts/${accountId}`);
  },

  async syncVkProfile(accountId: string): Promise<SocialAccount> {
    const response = await api.post<SocialAccount>(`/social/accounts/${accountId}/sync-profile`);
    return response.data;
  },

  // OAuth Apps
  async getOAuthApps(platform?: string): Promise<OAuthApp[]> {
    const url = platform ? `/social/oauth-apps?platform=${platform}` : "/social/oauth-apps";
    const response = await api.get<OAuthAppListResponse>(url);
    return response.data.apps;
  },

  async createOAuthApp(data: OAuthAppCreate): Promise<OAuthApp> {
    const response = await api.post<OAuthApp>("/social/oauth-apps", data);
    return response.data;
  },

  async updateOAuthApp(appId: string, data: OAuthAppUpdate): Promise<OAuthApp> {
    const response = await api.patch<OAuthApp>(`/social/oauth-apps/${appId}`, data);
    return response.data;
  },

  async deleteOAuthApp(appId: string): Promise<void> {
    await api.delete(`/social/oauth-apps/${appId}`);
  },
};
