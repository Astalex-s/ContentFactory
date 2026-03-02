import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Table, Column } from "../ui/components/Table";
import { Badge } from "../ui/components/Badge";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { contentService, type GeneratedContent } from "../services/content";
import { apiBaseURL } from "../services/api";
import { ImageModal } from "../ui/components/ImageModal";

export function ContentPage() {
  const navigate = useNavigate();
  const [content, setContent] = useState<GeneratedContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<{ src: string; alt: string } | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await contentService.getAllContent(1, 100);
        setContent(result.items);
      } catch {
        setError("Не удалось загрузить контент");
        setContent([]);
      } finally {
        setLoading(false);
      }
    };
    fetchContent();
  }, []);

  const renderPreview = (item: GeneratedContent) => {
    if (item.content_type === "text") {
      return (
        <div
          style={{
            width: 60,
            height: 60,
            backgroundColor: colors.primary[100],
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 24,
            color: colors.primary[600],
            fontWeight: 600,
          }}
        >
          Aa
        </div>
      );
    }

    if (item.content_type === "image" && item.file_path) {
      const src = `${apiBaseURL}/content/media/${item.file_path}`;
      return (
        <img
          src={src}
          alt="Preview"
          onClick={() => setModalImage({ src, alt: "Контент" })}
          style={{
            width: 60,
            height: 60,
            objectFit: "cover",
            borderRadius: 6,
            cursor: "zoom-in",
          }}
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Crect fill='%23e5e7eb' width='60' height='60'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%239ca3af' font-size='12'%3E🖼️%3C/text%3E%3C/svg%3E";
          }}
        />
      );
    }

    if (item.content_type === "video" && item.file_path) {
      return (
        <div style={{ position: "relative", width: 60, height: 60 }}>
          <video
        src={`${apiBaseURL}/content/media/${item.file_path}`}
        style={{
          width: 60,
          height: 60,
              objectFit: "cover",
              borderRadius: 6,
            }}
          />
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              width: 20,
              height: 20,
              backgroundColor: "rgba(0, 0, 0, 0.6)",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              fontSize: 10,
            }}
          >
            ▶
          </div>
        </div>
      );
    }

    return (
      <div
        style={{
          width: 60,
          height: 60,
          backgroundColor: colors.gray[200],
          borderRadius: 6,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 20,
        }}
      >
        ?
      </div>
    );
  };

  const columns: Column<GeneratedContent>[] = [
    {
      key: "preview",
      header: "Превью",
      width: "80px",
      render: renderPreview,
    },
    {
      key: "product_id",
      header: "Товар ID",
      render: (item) => item.product_id.slice(0, 8) + "...",
    },
    {
      key: "content_type",
      header: "Тип",
      render: (item) => {
        const typeLabels = { text: "Текст", image: "Изображение", video: "Видео" };
        return typeLabels[item.content_type] || item.content_type;
      },
    },
    {
      key: "platform",
      header: "Платформа",
      render: (item) => {
        const platformLabels: Record<string, string> = {
          youtube: "YouTube",
          vk: "VK",
        };
        return platformLabels[item.platform] || item.platform.toUpperCase();
      },
    },
    {
      key: "status",
      header: "Статус",
      render: (item) => {
        const statusVariants = {
          draft: "neutral" as const,
          ready: "success" as const,
          published: "info" as const,
        };
        const statusLabels = {
          draft: "Черновик",
          ready: "Готов",
          published: "Опубликован",
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
      header: "Создан",
      render: (item) => new Date(item.created_at).toLocaleDateString("ru-RU"),
    },
    {
      key: "approved",
      header: "Одобрен",
      render: (item) => {
        if (item.content_type !== "video" && item.content_type !== "image") return "—";
        return item.approved_for_publication ? "✓ Да" : "Нет";
      },
    },
  ];

  return (
    <PageContainer>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.lg }}>
        <h1 style={{ margin: 0 }}>Контент</h1>
        <Button variant="primary" onClick={() => navigate("/products")}>
          Создать контент
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {modalImage && (
        <ImageModal src={modalImage.src} alt={modalImage.alt} onClose={() => setModalImage(null)} />
      )}

      <Card title="Весь сгенерированный контент" padding="none">
        <Table
          data={content}
          columns={columns}
          isLoading={loading}
          emptyMessage="Контент ещё не создан. Перейдите к товарам и создайте контент."
          actions={(item) => (
            <div style={{ display: "flex", gap: spacing.sm, flexWrap: "wrap" }}>
              {(item.content_type === "video" || item.content_type === "image") && (
                <Button
                  variant={item.approved_for_publication ? "secondary" : "primary"}
                  size="sm"
                  onClick={async (e) => {
                    e?.stopPropagation();
                    try {
                      await contentService.setApprovedForPublication(
                        item.id,
                        !item.approved_for_publication
                      );
                      const result = await contentService.getAllContent(1, 100);
                      setContent(result.items);
                    } catch {
                      alert("Не удалось изменить одобрение");
                    }
                  }}
                >
                  {item.approved_for_publication ? "Снять одобрение" : "Одобрить"}
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e?.stopPropagation();
                  navigate(`/products/${item.product_id}/content`);
                }}
              >
                Просмотр
              </Button>
            </div>
          )}
        />
      </Card>
    </PageContainer>
  );
}
