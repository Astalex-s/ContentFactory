import { useState, useEffect, useMemo } from "react";
import { PageContainer } from "../ui/layout/PageContainer";
import { Card } from "../ui/components/Card";
import { Table, Column } from "../ui/components/Table";
import { Badge } from "../ui/components/Badge";
import { Button } from "../ui/components/Button";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { publishService, PublicationItem } from "../services/publishService";
import { analyticsApi } from "../features/analytics/api";
import { SchedulePublicationModal } from "../components/SchedulePublicationModal";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export function PublishingPage() {
  const [publications, setPublications] = useState<PublicationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    status: "",
    platform: "",
  });
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [fetchingStatsFor, setFetchingStatsFor] = useState<string | null>(null);

  useEffect(() => {
    loadPublications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const loadPublications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await publishService.getPublications({
        status: filters.status || undefined,
        platform: filters.platform || undefined,
        limit: 50,
      });
      setPublications(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load publications:", err);
      setError("Не удалось загрузить публикации");
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleSuccess = () => {
    loadPublications();
  };

  const [fetchStatsResult, setFetchStatsResult] = useState<string | null>(null);

  const handleFetchStats = async (item: PublicationItem) => {
    const videoId = item.platform_video_id;
    const canFetch =
      videoId && (item.status === "published" || item.status === "processing");
    if (!canFetch) return;
    setFetchStatsResult(null);
    setFetchingStatsFor(item.id);
    try {
      await analyticsApi.fetchAndRecordStats(
        item.content_id,
        item.platform,
        item.account_id,
        videoId
      );
      setFetchStatsResult(`Статистика обновлена: ${item.platform}`);
      loadPublications();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFetchStatsResult(detail || "Не удалось обновить статистику");
    } finally {
      setFetchingStatsFor(null);
    }
  };

  const handleCancelPublication = async (id: string) => {
    if (!confirm("Отменить эту публикацию?")) return;

    try {
      await publishService.cancelPublication(id);
      loadPublications();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail || "Не удалось отменить публикацию");
    }
  };

  const columns: Column<PublicationItem>[] = [
    {
      key: "preview",
      header: "Превью",
      render: (item) => {
        if (item.content_type === "video" && item.content_file_path) {
          return (
            <div
              style={{
                width: 120,
                height: 68,
                borderRadius: 6,
                overflow: "hidden",
                backgroundColor: colors.gray[100],
              }}
            >
              <video
                src={`${API_BASE_URL}/content/media/${item.content_file_path}`}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
                muted
                preload="metadata"
              />
            </div>
          );
        }
        return (
          <span style={{ color: colors.gray[500], fontSize: 12 }}>—</span>
        );
      },
    },
    {
      key: "content_id",
      header: "Content ID",
      render: (item) => (
        <span style={{ fontFamily: "monospace", fontSize: "13px" }}>
          {item.content_id.slice(0, 8)}...
        </span>
      ),
    },
    {
      key: "platform",
      header: "Платформа",
      render: (item) => (
        <Badge variant="neutral">{item.platform.toUpperCase()}</Badge>
      ),
    },
    {
      key: "scheduled_at",
      header: "Запланировано",
      render: (item) => {
        const date = new Date(item.scheduled_at);
        const now = new Date();
        const isPast = date < now;
        return (
          <div>
            <div>{date.toLocaleDateString("ru-RU")}</div>
            <div style={{ fontSize: "12px", color: colors.textSecondary }}>
              {date.toLocaleTimeString("ru-RU", {
                hour: "2-digit",
                minute: "2-digit",
              })}
              {isPast && item.status === "pending" && " (просрочено)"}
            </div>
          </div>
        );
      },
    },
    {
      key: "views",
      header: "Просмотры",
      render: (item) =>
        item.views != null ? item.views.toLocaleString("ru-RU") : "—",
    },
    {
      key: "status",
      header: "Статус",
      render: (item) => {
        const statusVariants = {
          pending: "neutral" as const,
          processing: "warning" as const,
          published: "success" as const,
          failed: "danger" as const,
        };
        const statusLabels = {
          pending: "Ожидает",
          processing: "В процессе",
          published: "Опубликовано",
          failed: "Ошибка",
        };
        return (
          <div>
            <Badge variant={statusVariants[item.status]}>
              {statusLabels[item.status]}
            </Badge>
            {item.error_message && (
              <div
                style={{
                  fontSize: "12px",
                  color: colors.danger,
                  marginTop: spacing.xs,
                }}
              >
                {item.error_message.slice(0, 50)}...
              </div>
            )}
          </div>
        );
      },
    },
    {
      key: "created_at",
      header: "Создано",
      render: (item) => new Date(item.created_at).toLocaleDateString("ru-RU"),
    },
    {
      key: "actions",
      header: "Действия",
      align: "right",
      render: (item) => (
        <div style={{ display: "flex", gap: spacing.xs, justifyContent: "flex-end" }}>
          {item.status === "pending" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleCancelPublication(item.id);
              }}
            >
              Отменить
            </Button>
          )}
          {(item.status === "published" || item.status === "processing") &&
            item.platform_video_id && (
            <Button
              variant="ghost"
              size="sm"
              disabled={fetchingStatsFor === item.id}
              onClick={(e) => {
                e.stopPropagation();
                handleFetchStats(item);
              }}
            >
              {fetchingStatsFor === item.id ? "…" : "Обновить статистику"}
            </Button>
          )}
          {item.platform_video_id && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                const urls: Record<string, string> = {
                  youtube: `https://youtube.com/watch?v=${item.platform_video_id}`,
                };
                const url = urls[item.platform];
                if (url) window.open(url, "_blank");
              }}
            >
              Открыть
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <PageContainer>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: spacing.sm,
          marginBottom: spacing.lg,
        }}
      >
        <div>
          <h1 style={{ margin: 0 }}>Публикации</h1>
          <p style={{ margin: `${spacing.xs} 0 0 0`, color: colors.textSecondary }}>
            Всего публикаций: {total}
          </p>
        </div>
        <Button
          type="button"
          variant="primary"
          size="sm"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setShowScheduleModal(true);
          }}
          style={{ whiteSpace: "nowrap", flexShrink: 0 }}
        >
          + Запланировать
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}
      {fetchStatsResult && (
        <Alert
          type={fetchStatsResult.startsWith("Статистика") ? "success" : "error"}
          onClick={() => setFetchStatsResult(null)}
        >
          {fetchStatsResult} (нажмите, чтобы закрыть)
        </Alert>
      )}

      {/* Filters */}
      <Card style={{ marginBottom: spacing.lg }}>
        <div style={{ display: "flex", gap: spacing.md, flexWrap: "wrap" }}>
          <div>
            <label
              style={{
                display: "block",
                marginBottom: spacing.xs,
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              Статус
            </label>
            <select
              value={filters.status}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, status: e.target.value }))
              }
              style={{
                padding: spacing.sm,
                borderRadius: "6px",
                border: `1px solid ${colors.border}`,
                minWidth: "150px",
              }}
            >
              <option value="">Все</option>
              <option value="pending">Ожидает</option>
              <option value="processing">В процессе</option>
              <option value="published">Опубликовано</option>
              <option value="failed">Ошибка</option>
            </select>
          </div>

          <div>
            <label
              style={{
                display: "block",
                marginBottom: spacing.xs,
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              Платформа
            </label>
            <select
              value={filters.platform}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, platform: e.target.value }))
              }
              style={{
                padding: spacing.sm,
                borderRadius: "6px",
                border: `1px solid ${colors.border}`,
                minWidth: "150px",
              }}
            >
              <option value="">Все</option>
              <option value="youtube">YouTube</option>
            </select>
          </div>

          {(filters.status || filters.platform) && (
            <div style={{ alignSelf: "flex-end" }}>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters({ status: "", platform: "" })}
              >
                Сбросить фильтры
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Publications Table */}
      <Card title="Очередь публикаций" padding="none">
        <Table
          data={publications}
          columns={columns}
          isLoading={loading}
          emptyMessage={
            filters.status || filters.platform
              ? "Нет публикаций с выбранными фильтрами"
              : "Нет запланированных публикаций. Нажмите 'Запланировать публикации' для создания."
          }
        />
      </Card>

      <SchedulePublicationModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
        selectedContent={useMemo(() => [], [])}
        onSuccess={handleScheduleSuccess}
      />
    </PageContainer>
  );
}
