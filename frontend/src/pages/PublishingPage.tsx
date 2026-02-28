import { useState, useEffect } from "react";
import { PageContainer } from "../ui/layout/PageContainer";
import { Card } from "../ui/components/Card";
import { Table, Column } from "../ui/components/Table";
import { Badge } from "../ui/components/Badge";
import { Button } from "../ui/components/Button";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { publishService, PublicationItem } from "../services/publishService";
import { ContentSelector } from "../components/ContentSelector";
import { SchedulePublicationModal } from "../components/SchedulePublicationModal";
import { GeneratedContent } from "../services/content";

export function PublishingPage() {
  const [publications, setPublications] = useState<PublicationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    status: "",
    platform: "",
  });
  const [showContentSelector, setShowContentSelector] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedContent, setSelectedContent] = useState<GeneratedContent[]>([]);

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

  const handleContentSelected = (content: GeneratedContent[]) => {
    setSelectedContent(content);
    setShowScheduleModal(true);
  };

  const handleScheduleSuccess = () => {
    loadPublications();
    setSelectedContent([]);
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
          {item.platform_video_id && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                const urls: Record<string, string> = {
                  youtube: `https://youtube.com/watch?v=${item.platform_video_id}`,
                  vk: `https://vk.com/video${item.platform_video_id}`,
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
          variant="primary"
          size="sm"
          onClick={() => setShowContentSelector(true)}
          style={{ whiteSpace: "nowrap", flexShrink: 0 }}
        >
          + Запланировать
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}

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
              <option value="vk">VK</option>
              <option value="tiktok">TikTok</option>
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

      {/* Modals */}
      <ContentSelector
        isOpen={showContentSelector}
        onClose={() => setShowContentSelector(false)}
        onSelect={handleContentSelected}
      />

      <SchedulePublicationModal
        isOpen={showScheduleModal}
        onClose={() => {
          setShowScheduleModal(false);
          setSelectedContent([]);
        }}
        selectedContent={selectedContent}
        onSuccess={handleScheduleSuccess}
      />
    </PageContainer>
  );
}
