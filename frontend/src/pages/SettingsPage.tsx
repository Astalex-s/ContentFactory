import { useState } from "react";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Select } from "../ui/components/Select";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";

export function SettingsPage() {
  const [defaultPlatform, setDefaultPlatform] = useState("youtube");
  const [autoPublish, setAutoPublish] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    setSuccess(false);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <PageContainer>
      <h1 style={{ marginBottom: spacing.lg }}>Настройки</h1>

      {success && <Alert type="success">Настройки сохранены</Alert>}

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
