import { useState } from "react";
import { useSocialAccounts } from "./useSocialAccounts";

const platformLabels: Record<string, string> = {
  youtube: "YouTube",
  vk: "VK",
  tiktok: "TikTok",
};

type Platform = "youtube" | "vk" | "tiktok";

const PLATFORMS: Platform[] = ["youtube", "vk", "tiktok"];

export function ConnectButton() {
  const { accounts, loading, error, connectPlatform, disconnectAccount } =
    useSocialAccounts();
  const [disconnectingId, setDisconnectingId] = useState<string | null>(null);

  const handleDisconnect = async (accountId: string) => {
    setDisconnectingId(accountId);
    try {
      await disconnectAccount(accountId);
    } finally {
      setDisconnectingId(null);
    }
  };

  return (
    <div style={{ padding: "1rem", border: "1px solid #ddd", borderRadius: 8 }}>
      <h3 style={{ marginTop: 0, marginBottom: "0.75rem" }}>Подключённые аккаунты</h3>
      {loading && <p style={{ color: "#666", fontSize: 14 }}>Загрузка...</p>}
      {error && (
        <p style={{ color: "#c00", fontSize: 14 }}>Ошибка: {error}</p>
      )}
      {!loading && !error && (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.5rem" }}>
            {accounts.map((a) => {
              const label = platformLabels[a.platform] ?? a.platform;
              const displayName = a.channel_title ? `${label}: ${a.channel_title}` : label;
              return (
                <span
                  key={a.id}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    padding: "0.25rem 0.5rem",
                    background: "#e8f5e9",
                    borderRadius: 4,
                    fontSize: 12,
                  }}
                >
                  {displayName}
                  <button
                    type="button"
                    onClick={() => handleDisconnect(a.id)}
                    disabled={disconnectingId === a.id}
                    title="Отключить"
                    style={{
                      padding: "0 0.25rem",
                      background: "transparent",
                      border: "none",
                      cursor: disconnectingId === a.id ? "default" : "pointer",
                      fontSize: 14,
                      color: "#c62828",
                      lineHeight: 1,
                    }}
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {PLATFORMS.map((p) => (
              <button
                key={p}
                onClick={() => connectPlatform(p)}
                style={{
                  padding: "0.25rem 0.75rem",
                  background: "#0066cc",
                  color: "#fff",
                  border: "none",
                  borderRadius: 4,
                  cursor: "pointer",
                  fontSize: 13,
                }}
              >
                Подключить {platformLabels[p]}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
