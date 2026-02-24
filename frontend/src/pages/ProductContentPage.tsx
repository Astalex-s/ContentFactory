import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { productsService } from "@/services/products";
import { contentApi } from "@/features/content";
import { ConnectButton, PublishModal, PublicationStatus } from "@/features/social";
import { apiBaseURL } from "@/services/api";
import type { Product } from "@/types/product";
import type { GeneratedContentItem } from "@/features/content";

const btnStyle: React.CSSProperties = {
  padding: "0.5rem 1rem",
  background: "#666",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
};

function getMediaUrl(filePath: string): string {
  return `${apiBaseURL}/content/media/${filePath}`;
}

export function ProductContentPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [contentList, setContentList] = useState<{
    items: GeneratedContentItem[];
    total: number;
  } | null>(null);
  const page = 1;
  const [genImagesLoading, setGenImagesLoading] = useState(false);
  const [genVideoLoading, setGenVideoLoading] = useState(false);
  const [genVideoImageId, setGenVideoImageId] = useState<string>("");
  const [publishModalContentId, setPublishModalContentId] = useState<string | null>(null);
  const [lastPublicationId, setLastPublicationId] = useState<string | null>(null);

  const fetchProduct = useCallback(async () => {
    if (!id) return;
    const p = await productsService.getProduct(id);
    setProduct(p ?? null);
  }, [id]);

  const fetchContent = useCallback(async () => {
    if (!id) return;
    const data = await contentApi.getContentByProduct(id, page, 50);
    setContentList(data);
  }, [id, page]);

  useEffect(() => {
    fetchProduct().finally(() => setLoading(false));
  }, [fetchProduct]);

  useEffect(() => {
    fetchContent();
  }, [fetchContent]);

  const pollTask = async (taskId: string, onDone: () => void) => {
    const maxAttempts = 120;
    for (let i = 0; i < maxAttempts; i++) {
      const { status } = await contentApi.getTaskStatus(taskId);
      if (status === "completed") {
        onDone();
        return;
      }
      if (status === "failed") {
        throw new Error("Генерация завершилась с ошибкой");
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
    throw new Error("Превышено время ожидания");
  };

  const handleGenerateImages = async () => {
    if (!id) return;
    setGenImagesLoading(true);
    try {
      const { task_id } = await contentApi.generateImages(id);
      await pollTask(task_id, () => fetchContent());
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setGenImagesLoading(false);
    }
  };

  const handleGenerateVideo = async () => {
    if (!id) return;
    setGenVideoLoading(true);
    try {
      const imageId = genVideoImageId || undefined;
      const { task_id } = await contentApi.generateVideo(id, imageId);
      await pollTask(task_id, () => fetchContent());
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setGenVideoLoading(false);
    }
  };

  const handleDelete = async (contentId: string) => {
    if (!window.confirm("Удалить этот контент?")) return;
    try {
      await contentApi.deleteContent(contentId);
      fetchContent();
    } catch {
      alert("Не удалось удалить");
    }
  };

  const images = contentList?.items.filter((c) => c.content_type === "image") ?? [];
  const videos = contentList?.items.filter((c) => c.content_type === "video") ?? [];

  if (loading || !id) {
    return (
      <div style={{ padding: "1.5rem", maxWidth: 900, margin: "0 auto" }}>
        <p>Загрузка...</p>
      </div>
    );
  }

  if (!product) {
    return (
      <div style={{ padding: "1.5rem", maxWidth: 900, margin: "0 auto" }}>
        <button onClick={() => navigate(-1)} style={btnStyle}>
          ← Назад
        </button>
        <p style={{ color: "#c00", marginTop: "1rem" }}>Товар не найден</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "1.5rem", maxWidth: 900, margin: "0 auto" }}>
      <button onClick={() => navigate(`/products/${id}`)} style={btnStyle}>
        ← К товару
      </button>
      <button
        onClick={() => navigate(`/products/${id}/generate`)}
        style={{ ...btnStyle, marginLeft: "0.5rem" }}
      >
        Сгенерировать текст
      </button>

      <h1 style={{ marginTop: "1.5rem", marginBottom: "1rem" }}>{product.name}</h1>
      <h2 style={{ fontSize: "1rem", color: "#666", marginBottom: "1rem" }}>
        Сгенерированный контент
      </h2>

      <section style={{ marginBottom: "1.5rem" }}>
        <ConnectButton />
      </section>

      <section
        style={{
          padding: "1rem",
          border: "1px solid #ddd",
          borderRadius: 8,
          marginBottom: "1.5rem",
        }}
      >
        <h3 style={{ marginTop: 0, marginBottom: "0.75rem" }}>Генерация медиа</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "flex-end" }}>
          <button
            onClick={handleGenerateImages}
            disabled={genImagesLoading}
            style={{
              ...btnStyle,
              background: genImagesLoading ? "#999" : "#0066cc",
            }}
          >
            {genImagesLoading ? "Генерация 3 изображений..." : "Сгенерировать 3 изображения"}
          </button>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 12, color: "#666" }}>По какой картинке видео</span>
            <select
              value={genVideoImageId}
              onChange={(e) => setGenVideoImageId(e.target.value)}
              disabled={genVideoLoading}
              style={{ padding: "0.5rem", minWidth: 180 }}
            >
              <option value="">Основное фото товара</option>
              {images.map((img) => (
                <option key={img.id} value={img.id}>
                  Изображение {img.content_variant}
                </option>
              ))}
            </select>
          </label>
          <button
            onClick={handleGenerateVideo}
            disabled={genVideoLoading}
            style={{
              ...btnStyle,
              background: genVideoLoading ? "#999" : "#28a745",
            }}
          >
            {genVideoLoading ? "Генерация видео..." : "Сгенерировать видео"}
          </button>
        </div>
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.75rem" }}>Изображения</h3>
        {images.length === 0 && <p style={{ color: "#666" }}>Нет изображений</p>}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
          {images.map((item) => (
            <div
              key={item.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: 8,
                overflow: "hidden",
                maxWidth: 240,
              }}
            >
              {item.file_path && (
                <img
                  src={getMediaUrl(item.file_path)}
                  alt={`Вариант ${item.content_variant}`}
                  style={{ width: "100%", height: 200, objectFit: "cover" }}
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.background = "#eee";
                  }}
                />
              )}
              <div style={{ padding: "0.5rem", fontSize: 12, color: "#888" }}>
                Вариант {item.content_variant}
              </div>
              <button
                onClick={() => handleDelete(item.id)}
                style={{ ...btnStyle, background: "#c00", margin: "0 0.5rem 0.5rem", padding: "0.25rem 0.5rem", fontSize: 12 }}
              >
                Удалить
              </button>
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.75rem" }}>Видео</h3>
        {lastPublicationId && (
          <PublicationStatus
            publicationId={lastPublicationId}
            onClose={() => setLastPublicationId(null)}
          />
        )}
        {videos.length === 0 && <p style={{ color: "#666" }}>Нет видео</p>}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {videos.map((item) => (
            <div
              key={item.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: 8,
                overflow: "hidden",
                maxWidth: 400,
              }}
            >
              {item.file_path && (
                <>
                  <video
                    src={getMediaUrl(item.file_path)}
                    controls
                    preload="auto"
                    playsInline
                    style={{ width: "100%", maxHeight: 400 }}
                  >
                    Ваш браузер не поддерживает воспроизведение видео.
                  </video>
                  <a
                    href={getMediaUrl(item.file_path)}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: 12, color: "#0066cc", marginTop: 4, display: "block" }}
                  >
                    Открыть видео в новой вкладке
                  </a>
                </>
              )}
              <div style={{ padding: "0.5rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                <span style={{ fontSize: 12, color: "#888" }}>Видео</span>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    onClick={() => setPublishModalContentId(item.id)}
                    style={{ ...btnStyle, background: "#28a745", padding: "0.25rem 0.5rem", fontSize: 12 }}
                  >
                    Опубликовать
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    style={{ ...btnStyle, background: "#c00", padding: "0.25rem 0.5rem", fontSize: 12 }}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {publishModalContentId && product && (
        <PublishModal
          contentId={publishModalContentId}
          productId={id!}
          productName={product.name}
          textContentItems={contentList?.items.filter((c) => c.content_type === "text") ?? []}
          onClose={() => setPublishModalContentId(null)}
          onPublished={(pubId) => {
            setLastPublicationId(pubId);
            setPublishModalContentId(null);
          }}
        />
      )}

      <section>
        <h3 style={{ marginBottom: "0.75rem" }}>Текстовый контент</h3>
        {contentList?.items.filter((c) => c.content_type === "text").length === 0 && (
          <p style={{ color: "#666" }}>Нет текстового контента</p>
        )}
        {contentList?.items
          .filter((c) => c.content_type === "text")
          .map((item) => (
            <div
              key={item.id}
              style={{
                padding: "1rem",
                border: "1px solid #ddd",
                borderRadius: 8,
                marginBottom: "0.75rem",
                background: "#fafafa",
              }}
            >
              <div style={{ fontSize: 12, color: "#888", marginBottom: "0.5rem" }}>
                {item.platform} • {item.tone} • {item.content_text_type} • вариант {item.content_variant}
              </div>
              <pre
                style={{
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  fontFamily: "inherit",
                  margin: "0 0 0.5rem 0",
                  fontSize: 14,
                }}
              >
                {item.content_text ?? "—"}
              </pre>
              <button
                onClick={() => handleDelete(item.id)}
                style={{ ...btnStyle, background: "#c00", padding: "0.25rem 0.5rem", fontSize: 12 }}
              >
                Удалить
              </button>
            </div>
          ))}
      </section>
    </div>
  );
}
