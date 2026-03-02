import { useState, useEffect, useCallback } from "react";
import { socialApi, getErrorMessage, type SocialAccount } from "./api";

function getOAuthErrorFromUrl(): string | null {
  const params = new URLSearchParams(window.location.search);
  if (params.get("social") === "error") {
    const msg = params.get("message");
    return msg ? decodeURIComponent(msg) : "Ошибка подключения";
  }
  return null;
}

export function useSocialAccounts() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(() => getOAuthErrorFromUrl());

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await socialApi.getAccounts();
      setAccounts(list);
    } catch (e) {
      setError(getErrorMessage(e));
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlError = getOAuthErrorFromUrl();
    if (urlError) {
      setError(urlError);
      // Очистить URL от OAuth-параметров
      params.delete("social");
      params.delete("message");
      const newSearch = params.toString();
      const newUrl = newSearch ? `${window.location.pathname}?${newSearch}` : window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    }
    if (params.get("social") === "connected") {
      params.delete("social");
      params.delete("platform");
      const newSearch = params.toString();
      const newUrl = newSearch ? `${window.location.pathname}?${newSearch}` : window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    }
    fetchAccounts();
  }, [fetchAccounts]);

  const connectPlatform = (platform: "youtube" | "vk") => {
    socialApi.getConnectUrl(platform).then((url) => {
      window.location.href = url;
    });
  };

  const disconnectAccount = async (accountId: string) => {
    try {
      await socialApi.disconnectAccount(accountId);
      await fetchAccounts();
    } catch (e) {
      setError(getErrorMessage(e));
    }
  };

  return {
    accounts,
    loading,
    error,
    refetch: fetchAccounts,
    connectPlatform,
    disconnectAccount,
  };
}
