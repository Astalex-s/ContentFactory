import { useState, useEffect } from "react";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Select } from "../ui/components/Select";
import { Alert } from "../ui/components/Alert";
import { Table, Column } from "../ui/components/Table";
import { spacing, colors } from "../ui/theme";
import { socialService, type OAuthApp, type OAuthAppCreate } from "../services/social";

export function SettingsPage() {
  const [defaultPlatform, setDefaultPlatform] = useState("youtube");
  const [autoPublish, setAutoPublish] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // OAuth Apps state
  const [oauthApps, setOAuthApps] = useState<OAuthApp[]>([]);
  const [loadingApps, setLoadingApps] = useState(true);
  const [appError, setAppError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addingApp, setAddingApp] = useState(false);
  const [deletingAppId, setDeletingAppId] = useState<string | null>(null);

  // Form state
  const [formPlatform, setFormPlatform] = useState("youtube");
  const [formName, setFormName] = useState("");
  const [formClientId, setFormClientId] = useState("");
  const [formClientSecret, setFormClientSecret] = useState("");
  const [formRedirectUri, setFormRedirectUri] = useState("");

  const fetchOAuthApps = async () => {
    setLoadingApps(true);
    setAppError(null);
    try {
      const apps = await socialService.getOAuthApps();
      setOAuthApps(apps);
    } catch {
      setAppError("Не удалось загрузить OAuth-приложения");
      setOAuthApps([]);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    fetchOAuthApps();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSuccess(false);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  const handleAddApp = async () => {
    if (!formName.trim() || !formClientId.trim() || !formClientSecret.trim()) {
      setAppError("Заполните все обязательные поля");
      return;
    }

    setAddingApp(true);
    setAppError(null);
    try {
      const data: OAuthAppCreate = {
        platform: formPlatform,
        name: formName.trim(),
        client_id: formClientId.trim(),
        client_secret: formClientSecret.trim(),
        redirect_uri: formRedirectUri.trim() || undefined,
      };
      await socialService.createOAuthApp(data);
      setFormName("");
      setFormClientId("");
      setFormClientSecret("");
      setFormRedirectUri("");
      setShowAddForm(false);
      await fetchOAuthApps();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setAppError(detail || "Не удалось добавить OAuth-приложение");
    } finally {
      setAddingApp(false);
    }
  };

  const handleDeleteApp = async (id: string, name: string) => {
    if (!window.confirm(`Удалить OAuth-приложение "${name}"?`)) return;
    setDeletingAppId(id);
    setAppError(null);
    try {
      await socialService.deleteOAuthApp(id);
      await fetchOAuthApps();
    } catch {
      setAppError("Не удалось удалить OAuth-приложение");
    } finally {
      setDeletingAppId(null);
    }
  };

  const oauthColumns: Column<OAuthApp>[] = [
    {
      key: "platform",
      header: "Платформа",
      render: (app) => {
        const platformLabels: Record<string, string> = {
          youtube: "YouTube",
          vk: "VK",
          tiktok: "TikTok",
        };
        return platformLabels[app.platform] || app.platform.toUpperCase();
      },
    },
    {
      key: "name",
      header: "Название",
      render: (app) => <span style={{ fontWeight: 500 }}>{app.name}</span>,
    },
    {
      key: "client_id_masked",
      header: "Client ID",
      render: (app) => <span style={{ fontFamily: "monospace", fontSize: 13 }}>{app.client_id_masked}</span>,
    },
    {
      key: "created_at",
      header: "Создано",
      render: (app) => new Date(app.created_at).toLocaleDateString("ru-RU"),
    },
  ];

  return (
    <PageContainer>
      <h1 style={{ marginBottom: spacing.lg }}>Настройки</h1>

      {success && <Alert type="success">Настройки сохранены</Alert>}
      {appError && <Alert type="error">{appError}</Alert>}

      <Card title="OAuth-приложения для подключения аккаунтов" style={{ marginBottom: spacing.lg }}>
        <div style={{ marginBottom: spacing.md }}>
          <p style={{ fontSize: 14, color: colors.gray[500], marginBottom: spacing.md }}>
            Добавьте учётные данные OAuth-приложений для подключения аккаунтов YouTube, VK и TikTok.
            Все данные хранятся в зашифрованном виде.
          </p>
          {!showAddForm && (
            <Button variant="primary" onClick={() => setShowAddForm(true)} style={{ width: "auto" }}>
              + Добавить OAuth-приложение
            </Button>
          )}
        </div>

        {showAddForm && (
          <div style={{ marginBottom: spacing.lg, padding: spacing.md, border: `1px solid ${colors.gray[200]}`, borderRadius: 8 }}>
            <h3 style={{ marginBottom: spacing.md, fontSize: 16, fontWeight: 600 }}>Новое OAuth-приложение</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
              <Select label="Платформа *" value={formPlatform} onChange={(e) => setFormPlatform(e.target.value)}>
                <option value="youtube">YouTube</option>
                <option value="vk">VK</option>
                <option value="tiktok">TikTok</option>
              </Select>
              <div>
                <label style={{ display: "block", marginBottom: spacing.xs, fontSize: 14, fontWeight: 500 }}>
                  Название *
                </label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="Например: Мое YouTube приложение"
                  style={{ width: "100%", padding: "10px 12px", border: `1px solid ${colors.gray[300]}`, borderRadius: 6, fontSize: 14 }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: spacing.xs, fontSize: 14, fontWeight: 500 }}>
                  Client ID *
                </label>
                <input
                  type="text"
                  value={formClientId}
                  onChange={(e) => setFormClientId(e.target.value)}
                  placeholder="Введите Client ID"
                  style={{ width: "100%", padding: "10px 12px", border: `1px solid ${colors.gray[300]}`, borderRadius: 6, fontSize: 14, fontFamily: "monospace" }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: spacing.xs, fontSize: 14, fontWeight: 500 }}>
                  Client Secret *
                </label>
                <input
                  type="password"
                  value={formClientSecret}
                  onChange={(e) => setFormClientSecret(e.target.value)}
                  placeholder="Введите Client Secret"
                  style={{ width: "100%", padding: "10px 12px", border: `1px solid ${colors.gray[300]}`, borderRadius: 6, fontSize: 14, fontFamily: "monospace" }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: spacing.xs, fontSize: 14, fontWeight: 500 }}>
                  Redirect URI (опционально)
                </label>
                <input
                  type="text"
                  value={formRedirectUri}
                  onChange={(e) => setFormRedirectUri(e.target.value)}
                  placeholder="Оставьте пустым для использования по умолчанию"
                  style={{ width: "100%", padding: "10px 12px", border: `1px solid ${colors.gray[300]}`, borderRadius: 6, fontSize: 14, fontFamily: "monospace" }}
                />
              </div>
              <div style={{ display: "flex", gap: spacing.sm }}>
                <Button variant="primary" onClick={handleAddApp} loading={addingApp} style={{ width: "auto" }}>
                  Сохранить
                </Button>
                <Button variant="secondary" onClick={() => { setShowAddForm(false); setAppError(null); }} disabled={addingApp} style={{ width: "auto" }}>
                  Отмена
                </Button>
              </div>
            </div>
          </div>
        )}

        <Table
          data={oauthApps}
          columns={oauthColumns}
          isLoading={loadingApps}
          emptyMessage="Нет добавленных OAuth-приложений. Добавьте приложение для подключения аккаунтов."
          actions={(app) => (
            <Button
              variant="danger"
              size="sm"
              onClick={(e) => {
                e?.stopPropagation();
                handleDeleteApp(app.id, app.name);
              }}
              loading={deletingAppId === app.id}
              disabled={deletingAppId === app.id}
            >
              Удалить
            </Button>
          )}
        />
      </Card>

      <Card title="Публикация" style={{ marginBottom: spacing.lg }}>
        <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
          <div>
            <Select
              label="Платформа по умолчанию"
              value={defaultPlatform}
              onChange={(e) => setDefaultPlatform(e.target.value)}
            >
              <option value="youtube">YouTube</option>
              <option value="vk">VK</option>
              <option value="tiktok">TikTok</option>
            </Select>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
            <input
              type="checkbox"
              id="auto-publish"
              checked={autoPublish}
              onChange={(e) => setAutoPublish(e.target.checked)}
              style={{ width: 18, height: 18 }}
            />
            <label
              htmlFor="auto-publish"
              style={{ fontSize: 14, fontWeight: 500, color: colors.gray[700], cursor: "pointer" }}
            >
              Автоматическая публикация после генерации
            </label>
          </div>
        </div>
      </Card>

      <Card title="Уведомления" style={{ marginBottom: spacing.lg }}>
        <div style={{ display: "flex", flexDirection: "column", gap: spacing.sm }}>
          <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
            <input type="checkbox" id="notify-errors" defaultChecked style={{ width: 18, height: 18 }} />
            <label
              htmlFor="notify-errors"
              style={{ fontSize: 14, fontWeight: 500, color: colors.gray[700], cursor: "pointer" }}
            >
              Уведомлять об ошибках
            </label>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
            <input type="checkbox" id="notify-success" style={{ width: 18, height: 18 }} />
            <label
              htmlFor="notify-success"
              style={{ fontSize: 14, fontWeight: 500, color: colors.gray[700], cursor: "pointer" }}
            >
              Уведомлять об успешных публикациях
            </label>
          </div>
        </div>
      </Card>

      <Button variant="primary" onClick={handleSave} loading={saving} style={{ width: "auto" }}>
        Сохранить настройки
      </Button>
    </PageContainer>
  );
}
