import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Table, Column } from "../ui/components/Table";
import { Badge } from "../ui/components/Badge";
import { Alert } from "../ui/components/Alert";
import { Select } from "../ui/components/Select";
import { spacing, colors } from "../ui/theme";
import { socialService, type SocialAccount, type OAuthApp } from "../services/social";

export function CreatorsPage() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState("youtube");
  const [connecting, setConnecting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // OAuth Apps state
  const [oauthApps, setOAuthApps] = useState<OAuthApp[]>([]);
  const [loadingApps, setLoadingApps] = useState(true);
  const [selectedAppId, setSelectedAppId] = useState<string>("");

  const fetchAccounts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await socialService.getAccounts();
      setAccounts(data);
    } catch (err) {
      setError("Не удалось загрузить аккаунты");
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchOAuthApps = async () => {
    setLoadingApps(true);
    try {
      const apps = await socialService.getOAuthApps();
      setOAuthApps(apps);
      if (apps.length > 0 && !selectedAppId) {
        setSelectedAppId(apps[0].id);
      }
    } catch (err) {
      setOAuthApps([]);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
    fetchOAuthApps();
  }, []);

  const handleConnect = async () => {
    if (!selectedAppId) {
      setError("Выберите OAuth-приложение или добавьте новое в настройках");
      return;
    }
    setConnecting(true);
    setError(null);
    try {
      const authUrl = await socialService.connectPlatform(selectedPlatform, selectedAppId);
      window.location.href = authUrl;
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Не удалось подключить аккаунт");
      setConnecting(false);
    }
  };

  const platformApps = oauthApps.filter((app) => app.platform === selectedPlatform);

  const handleDelete = async (id: string, title: string) => {
    if (!window.confirm(`Удалить аккаунт ${title}?`)) return;
    setDeletingId(id);
    setError(null);
    try {
      await socialService.disconnectAccount(id);
      await fetchAccounts();
    } catch (err) {
      setError("Не удалось удалить аккаунт");
    } finally {
      setDeletingId(null);
    }
  };

  const columns: Column<SocialAccount>[] = [
    {
      key: "platform",
      header: "Платформа",
      render: (acc) => {
        const platformLabels: Record<string, string> = {
          youtube: "YouTube",
          vk: "VK",
          tiktok: "TikTok",
        };
        return platformLabels[acc.platform] || acc.platform.toUpperCase();
      },
    },
    {
      key: "channel_title",
      header: "Название канала",
      render: (acc) => <span style={{ fontWeight: 500 }}>{acc.channel_title || acc.channel_id || "—"}</span>,
    },
    {
      key: "channel_id",
      header: "ID канала",
      render: (acc) => acc.channel_id || "—",
    },
    {
      key: "status",
      header: "Статус",
      render: () => (
        <Badge variant="success">
          Активен
        </Badge>
      ),
    },
    {
      key: "created_at",
      header: "Подключен",
      render: (acc) => acc.created_at ? new Date(acc.created_at).toLocaleDateString("ru-RU") : "—",
    },
  ];

  return (
    <PageContainer>
      <h1 style={{ marginBottom: spacing.lg }}>Подключенные аккаунты</h1>

      {error && <Alert type="error">{error}</Alert>}

      <Card title="Подключить новый аккаунт" style={{ marginBottom: spacing.lg }}>
        <div style={{ display: "flex", gap: spacing.md, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ minWidth: 200, flex: 1 }}>
            <Select
              label="Платформа"
              value={selectedPlatform}
              onChange={(e) => {
                setSelectedPlatform(e.target.value);
                const apps = oauthApps.filter((app) => app.platform === e.target.value);
                if (apps.length > 0) {
                  setSelectedAppId(apps[0].id);
                } else {
                  setSelectedAppId("");
                }
              }}
            >
              <option value="youtube">YouTube</option>
              <option value="vk">VK</option>
              <option value="tiktok">TikTok</option>
            </Select>
          </div>
          <div style={{ minWidth: 250, flex: 1 }}>
            <Select
              label="OAuth-приложение"
              value={selectedAppId}
              onChange={(e) => setSelectedAppId(e.target.value)}
              disabled={loadingApps || platformApps.length === 0}
            >
              {platformApps.length === 0 ? (
                <option value="">Нет доступных приложений</option>
              ) : (
                platformApps.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.name}
                  </option>
                ))
              )}
            </Select>
          </div>
          <Button variant="primary" onClick={handleConnect} loading={connecting} disabled={!selectedAppId} style={{ height: "42px" }}>
            Подключить
          </Button>
        </div>
        {platformApps.length === 0 && !loadingApps && (
          <div style={{ marginTop: spacing.md, padding: spacing.md, backgroundColor: colors.warningShades[50], border: `1px solid ${colors.warningShades[200]}`, borderRadius: 6 }}>
            <p style={{ fontSize: 14, color: colors.warningShades[800], marginBottom: spacing.sm }}>
              Для платформы {selectedPlatform.toUpperCase()} нет добавленных OAuth-приложений.
            </p>
            <Button variant="secondary" onClick={() => navigate("/settings")} style={{ width: "auto", fontSize: 13 }}>
              Перейти в настройки
            </Button>
          </div>
        )}
        <div style={{ marginTop: spacing.sm, fontSize: 14, color: colors.gray[500] }}>
          После нажатия вы будете перенаправлены на страницу авторизации выбранной платформы
        </div>
      </Card>

      <Card title="Аккаунты социальных сетей" padding="none">
        <Table
          data={accounts}
          columns={columns}
          isLoading={loading}
          emptyMessage="Нет подключенных аккаунтов. Добавьте аккаунт для публикации контента."
          actions={(acc) => (
            <Button
              variant="danger"
              size="sm"
              onClick={(e) => {
                e?.stopPropagation();
                handleDelete(acc.id, acc.channel_title || acc.channel_id || "аккаунт");
              }}
              loading={deletingId === acc.id}
              disabled={deletingId === acc.id}
            >
              Удалить
            </Button>
          )}
        />
      </Card>
    </PageContainer>
  );
}
