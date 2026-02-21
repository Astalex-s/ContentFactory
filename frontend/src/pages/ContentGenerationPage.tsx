import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { productsService } from "@/services/products";
import {
  contentApi,
  useGenerateContent,
} from "@/features/content";
import type { Product } from "@/types/product";
import type { ContentTextType, Platform, Tone } from "@/features/content";

const PLATFORMS: { value: Platform; label: string }[] = [
  { value: "youtube", label: "YouTube" },
  { value: "vk", label: "ВКонтакте" },
  { value: "rutube", label: "Rutube" },
];

const TONES: { value: Tone; label: string }[] = [
  { value: "neutral", label: "Нейтральный" },
  { value: "emotional", label: "Эмоциональный" },
  { value: "expert", label: "Экспертный" },
];

const TEXT_TYPES: { value: ContentTextType; label: string }[] = [
  { value: "short_post", label: "Короткий пост" },
  { value: "video_description", label: "Видеоописание" },
  { value: "cta", label: "CTA" },
  { value: "all", label: "Всё вместе" },
];

const btnStyle: React.CSSProperties = {
  padding: "0.5rem 1rem",
  background: "#666",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
};

export function ContentGenerationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [contentList, setContentList] = useState<Awaited<ReturnType<typeof contentApi.getContentByProduct>> | null>(null);
  const [page, setPage] = useState(1);
  const [platform, setPlatform] = useState<Platform>("youtube");
  const [tone, setTone] = useState<Tone>("emotional");
  const [contentTextType, setContentTextType] = useState<ContentTextType>("short_post");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const { generate, loading: generating, error: generateError } = useGenerateContent(id);

  const fetchProduct = useCallback(async () => {
    if (!id) return;
    const p = await productsService.getProduct(id);
    setProduct(p ?? null);
  }, [id]);

  const fetchContent = useCallback(async () => {
    if (!id) return;
    const data = await contentApi.getContentByProduct(id, page, 10);
    setContentList(data);
  }, [id, page]);

  useEffect(() => {
    fetchProduct().finally(() => setLoading(false));
  }, [fetchProduct]);

  useEffect(() => {
    fetchContent();
  }, [fetchContent]);

  const handleGenerate = async () => {
    await generate(platform, tone, contentTextType);
    fetchContent();
  };

  const handleEdit = (item: { id: string; content_text: string | null }) => {
    setEditingId(item.id);
    setEditText(item.content_text ?? "");
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;
    try {
      await contentApi.updateContent(editingId, editText);
      setEditingId(null);
      fetchContent();
    } catch {
      // error handled by interceptor
    }
  };

  const handleDelete = async (contentId: string) => {
    if (!window.confirm("Удалить этот контент?")) return;
    try {
      await contentApi.deleteContent(contentId);
      fetchContent();
    } catch {
      // error handled by interceptor
    }
  };

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
        <button onClick={() => navigate(-1)} style={btnStyle}>← Назад</button>
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
        onClick={() => navigate(`/products/${id}/content`)}
        style={{ ...btnStyle, marginLeft: "0.5rem" }}
      >
        Просмотреть контент
      </button>

      <h1 style={{ marginTop: "1.5rem", marginBottom: "1rem" }}>{product.name}</h1>
      <h2 style={{ fontSize: "1rem", color: "#666", marginBottom: "1rem" }}>
        Генерация контента
      </h2>

      <section
        style={{
          padding: "1rem",
          border: "1px solid #ddd",
          borderRadius: 8,
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
          <label>
            <span style={{ fontSize: 14, color: "#666", display: "block", marginBottom: 4 }}>
              Платформа
            </span>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value as Platform)}
              disabled={generating}
              style={{ padding: "0.5rem", minWidth: 140 }}
            >
              {PLATFORMS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span style={{ fontSize: 14, color: "#666", display: "block", marginBottom: 4 }}>
              Тон
            </span>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value as Tone)}
              disabled={generating}
              style={{ padding: "0.5rem", minWidth: 140 }}
            >
              {TONES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span style={{ fontSize: 14, color: "#666", display: "block", marginBottom: 4 }}>
              Тип текста
            </span>
            <select
              value={contentTextType}
              onChange={(e) => setContentTextType(e.target.value as ContentTextType)}
              disabled={generating}
              style={{ padding: "0.5rem", minWidth: 160 }}
            >
              {TEXT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </label>
        </div>
        {generateError && (
          <p style={{ color: "#c00", marginBottom: "0.5rem" }}>{generateError}</p>
        )}
        <button
          onClick={handleGenerate}
          disabled={generating}
          style={{
            ...btnStyle,
            background: generating ? "#999" : "#333",
            padding: "0.75rem 1.5rem",
          }}
        >
          {generating ? "Генерация..." : "Сгенерировать"}
        </button>
      </section>

      <section>
        <h3 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>Созданный контент</h3>
        {contentList?.items.length === 0 && (
          <p style={{ color: "#666" }}>Пока нет контента. Нажмите «Сгенерировать».</p>
        )}
        {contentList?.items.map((item) => (
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
            {editingId === item.id ? (
              <div>
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  rows={6}
                  style={{ width: "100%", padding: "0.5rem", marginBottom: "0.5rem" }}
                />
                <button onClick={handleSaveEdit} style={btnStyle}>Сохранить</button>
                <button
                  onClick={() => setEditingId(null)}
                  style={{ ...btnStyle, marginLeft: "0.5rem", background: "#666" }}
                >
                  Отмена
                </button>
              </div>
            ) : (
              <>
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
                {item.status === "draft" && (
                  <div>
                    <button
                      onClick={() => handleEdit(item)}
                      style={{ ...btnStyle, padding: "0.25rem 0.5rem", fontSize: 13 }}
                    >
                      Редактировать
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      style={{
                        ...btnStyle,
                        padding: "0.25rem 0.5rem",
                        fontSize: 13,
                        marginLeft: "0.5rem",
                        background: "#c00",
                      }}
                    >
                      Удалить
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        ))}
        {contentList && contentList.total > 10 && (
          <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              style={btnStyle}
            >
              ← Назад
            </button>
            <span style={{ alignSelf: "center" }}>
              {page} / {Math.ceil(contentList.total / 10)}
            </span>
            <button
              disabled={page >= Math.ceil(contentList.total / 10)}
              onClick={() => setPage((p) => p + 1)}
              style={btnStyle}
            >
              Вперёд →
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
