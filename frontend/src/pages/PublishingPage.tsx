import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "../ui/layout/PageContainer";
import { Card } from "../ui/components/Card";
import { Table, Column } from "../ui/components/Table";
import { Badge } from "../ui/components/Badge";
import { Button } from "../ui/components/Button";
import { Alert } from "../ui/components/Alert";
import { spacing } from "../ui/theme";

interface PublicationItem {
  id: string;
  content_id: string;
  platform: string;
  scheduled_at: string;
  status: "pending" | "processing" | "published" | "failed";
  error_message?: string;
  created_at: string;
}

export function PublishingPage() {
  const navigate = useNavigate();
  const [publications, setPublications] = useState<PublicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error] = useState<string | null>(null);

  useEffect(() => {
    setLoading(false);
    setPublications([]);
  }, []);

  const columns: Column<PublicationItem>[] = [
    {
      key: "content_id",
      header: "Content ID",
      render: (item) => item.content_id.slice(0, 8) + "...",
    },
    {
      key: "platform",
      header: "Платформа",
      render: (item) => item.platform.toUpperCase(),
    },
    {
      key: "scheduled_at",
      header: "Запланировано",
      render: (item) => new Date(item.scheduled_at).toLocaleString("ru-RU"),
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
          <Badge variant={statusVariants[item.status]}>
            {statusLabels[item.status]}
          </Badge>
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
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            alert(`Детали публикации: ${item.id}`);
          }}
        >
          Детали
        </Button>
      ),
    },
  ];

  return (
    <PageContainer>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.lg }}>
        <h1 style={{ margin: 0 }}>Публикации</h1>
        <Button variant="primary" onClick={() => navigate("/products")}>
          Создать публикацию
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      <Card title="Очередь публикаций" padding="none">
        <Table
          data={publications}
          columns={columns}
          isLoading={loading}
          emptyMessage="Нет запланированных публикаций."
        />
      </Card>
    </PageContainer>
  );
}
