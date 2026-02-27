import { useState, useEffect } from "react";
import { Button } from "../ui/components/Button";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { publishService, PublicationScheduleItem } from "../services/publishService";
import { socialService, SocialAccount } from "../services/social";
import { GeneratedContent } from "../services/content";

interface SchedulePublicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: GeneratedContent[];
  onSuccess: () => void;
}

interface ScheduleItem extends PublicationScheduleItem {
  contentTitle: string;
}

export function SchedulePublicationModal({
  isOpen,
  onClose,
  selectedContent,
  onSuccess,
}: SchedulePublicationModalProps) {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadAccounts();
      initializeSchedules();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, selectedContent]);

  const loadAccounts = async () => {
    try {
      const data = await socialService.getAccounts();
      setAccounts(data);
    } catch (err) {
      console.error("Failed to load accounts:", err);
      setError("Не удалось загрузить подключённые аккаунты");
    }
  };

  const initializeSchedules = () => {
    const now = new Date();
    const items = selectedContent.map((content, index) => {
      const scheduledTime = new Date(now.getTime() + (index + 1) * 60 * 60 * 1000); // +1 hour for each
      return {
        content_id: content.id,
        platform: "",
        account_id: "",
        scheduled_at: scheduledTime.toISOString().slice(0, 16),
        title: "",
        description: content.content_text || "",
        contentTitle: `Контент ${content.content_type} (${content.platform})`,
      };
    });
    setSchedules(items);
  };

  const updateSchedule = (index: number, field: keyof ScheduleItem, value: string) => {
    setSchedules((prev) =>
      prev.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      )
    );
  };

  const handleSubmit = async () => {
    setError(null);

    // Validate
    for (const schedule of schedules) {
      if (!schedule.platform || !schedule.account_id) {
        setError("Выберите платформу и аккаунт для всех публикаций");
        return;
      }
    }

    setLoading(true);
    try {
      await publishService.bulkSchedulePublications({
        publications: schedules.map((s) => ({
          content_id: s.content_id,
          platform: s.platform,
          account_id: s.account_id,
          scheduled_at: new Date(s.scheduled_at).toISOString(),
          title: s.title || undefined,
          description: s.description || undefined,
        })),
      });
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "Не удалось запланировать публикации");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const platformAccounts = (platform: string) =>
    accounts.filter((a) => a.platform === platform);

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "12px",
          padding: spacing.xl,
          maxWidth: "800px",
          width: "90%",
          maxHeight: "90vh",
          overflow: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0 }}>Запланировать публикации</h2>
        <p style={{ color: colors.textSecondary }}>
          Выбрано контента: {selectedContent.length}
        </p>

        {error && <Alert type="error">{error}</Alert>}

        <div style={{ marginTop: spacing.lg }}>
          {schedules.map((schedule, index) => (
            <div
              key={schedule.content_id}
              style={{
                border: `1px solid ${colors.border}`,
                borderRadius: "8px",
                padding: spacing.md,
                marginBottom: spacing.md,
              }}
            >
              <h4 style={{ marginTop: 0, marginBottom: spacing.sm }}>
                {schedule.contentTitle}
              </h4>

              <div style={{ display: "grid", gap: spacing.md }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      marginBottom: spacing.xs,
                      fontWeight: 500,
                    }}
                  >
                    Платформа *
                  </label>
                  <select
                    value={schedule.platform}
                    onChange={(e) =>
                      updateSchedule(index, "platform", e.target.value)
                    }
                    style={{
                      width: "100%",
                      padding: spacing.sm,
                      borderRadius: "6px",
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <option value="">Выберите платформу</option>
                    <option value="youtube">YouTube</option>
                    <option value="vk">VK</option>
                    <option value="tiktok">TikTok</option>
                  </select>
                </div>

                {schedule.platform && (
                  <div>
                    <label
                      style={{
                        display: "block",
                        marginBottom: spacing.xs,
                        fontWeight: 500,
                      }}
                    >
                      Аккаунт *
                    </label>
                    <select
                      value={schedule.account_id}
                      onChange={(e) =>
                        updateSchedule(index, "account_id", e.target.value)
                      }
                      style={{
                        width: "100%",
                        padding: spacing.sm,
                        borderRadius: "6px",
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      <option value="">Выберите аккаунт</option>
                      {platformAccounts(schedule.platform).map((acc) => (
                        <option key={acc.id} value={acc.id}>
                          {acc.channel_title || acc.platform.toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label
                    style={{
                      display: "block",
                      marginBottom: spacing.xs,
                      fontWeight: 500,
                    }}
                  >
                    Дата и время публикации *
                  </label>
                  <input
                    type="datetime-local"
                    value={schedule.scheduled_at}
                    onChange={(e) =>
                      updateSchedule(index, "scheduled_at", e.target.value)
                    }
                    style={{
                      width: "100%",
                      padding: spacing.sm,
                      borderRadius: "6px",
                      border: `1px solid ${colors.border}`,
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      marginBottom: spacing.xs,
                      fontWeight: 500,
                    }}
                  >
                    Заголовок
                  </label>
                  <input
                    type="text"
                    value={schedule.title}
                    onChange={(e) =>
                      updateSchedule(index, "title", e.target.value)
                    }
                    placeholder="Оставьте пустым для автоматического"
                    maxLength={100}
                    style={{
                      width: "100%",
                      padding: spacing.sm,
                      borderRadius: "6px",
                      border: `1px solid ${colors.border}`,
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      marginBottom: spacing.xs,
                      fontWeight: 500,
                    }}
                  >
                    Описание
                  </label>
                  <textarea
                    value={schedule.description}
                    onChange={(e) =>
                      updateSchedule(index, "description", e.target.value)
                    }
                    rows={3}
                    maxLength={5000}
                    style={{
                      width: "100%",
                      padding: spacing.sm,
                      borderRadius: "6px",
                      border: `1px solid ${colors.border}`,
                      fontFamily: "inherit",
                      resize: "vertical",
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div
          style={{
            display: "flex",
            gap: spacing.md,
            marginTop: spacing.lg,
            justifyContent: "flex-end",
          }}
        >
          <Button variant="ghost" onClick={onClose} disabled={loading}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Планирование..." : "Запланировать"}
          </Button>
        </div>
      </div>
    </div>
  );
}
