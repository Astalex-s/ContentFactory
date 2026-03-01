import { useState, useEffect } from "react";
import { Button } from "../ui/components/Button";
import { Alert } from "../ui/components/Alert";
import { Badge } from "../ui/components/Badge";
import { spacing, colors } from "../ui/theme";
import { contentService, GeneratedContent } from "../services/content";

interface ContentSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (selected: GeneratedContent[]) => void;
  /** Только видео — для планирования публикаций */
  videoOnly?: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export function ContentSelector({
  isOpen,
  onClose,
  onSelect,
  videoOnly = false,
}: ContentSelectorProps) {
  const [content, setContent] = useState<GeneratedContent[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedText, setExpandedText] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<{
    type: string;
    platform: string;
  }>({
    type: "all",
    platform: "all",
  });

  useEffect(() => {
    if (isOpen) {
      loadContent();
      setSelected(new Set());
      setExpandedText(new Set());
    }
  }, [isOpen]);

  const loadContent = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await contentService.getAllContent(1, 100);
      // Filter content:
      // - Video/Image: only ready status
      // - Text: ready or draft (text is always ready to publish)
      const filtered = data.items.filter((item) => {
        if (item.content_type === "text") {
          return item.status === "ready" || item.status === "draft";
        }
        return item.status === "ready";
      });
      setContent(filtered);
    } catch (err) {
      console.error("Failed to load content:", err);
      setError("Не удалось загрузить контент");
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === filteredContent.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredContent.map((c) => c.id)));
    }
  };

  const handleConfirm = () => {
    const selectedContent = content.filter((c) => selected.has(c.id));
    onSelect(selectedContent);
    onClose();
  };

  const toggleExpandText = (id: string) => {
    setExpandedText((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const filteredContent = content.filter((item) => {
    if (videoOnly && item.content_type !== "video") return false;
    if (filter.type !== "all" && item.content_type !== filter.type) {
      return false;
    }
    if (filter.platform !== "all" && item.platform !== filter.platform) {
      return false;
    }
    return true;
  });

  if (!isOpen) return null;

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
          maxWidth: "900px",
          width: "90%",
          maxHeight: "90vh",
          overflow: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0 }}>Выбрать контент для публикации</h2>

        {error && <Alert type="error">{error}</Alert>}

        {/* Filters */}
        <div
          style={{
            display: "flex",
            gap: spacing.md,
            marginBottom: spacing.lg,
            flexWrap: "wrap",
          }}
        >
          <div>
            <label
              style={{
                display: "block",
                marginBottom: spacing.xs,
                fontSize: "14px",
                fontWeight: 500,
              }}
            >
              Тип контента
            </label>
            <select
              value={filter.type}
              onChange={(e) =>
                setFilter((prev) => ({ ...prev, type: e.target.value }))
              }
              style={{
                padding: spacing.sm,
                borderRadius: "6px",
                border: `1px solid ${colors.border}`,
              }}
            >
              <option value="all">Все</option>
              <option value="video">Видео</option>
              <option value="image">Изображения</option>
              <option value="text">Текст</option>
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
              value={filter.platform}
              onChange={(e) =>
                setFilter((prev) => ({ ...prev, platform: e.target.value }))
              }
              style={{
                padding: spacing.sm,
                borderRadius: "6px",
                border: `1px solid ${colors.border}`,
              }}
            >
              <option value="all">Все</option>
              <option value="youtube">YouTube</option>
              <option value="vk">VK</option>
              <option value="tiktok">TikTok</option>
            </select>
          </div>

          <div style={{ marginLeft: "auto", alignSelf: "flex-end" }}>
            <Button variant="ghost" size="sm" onClick={toggleSelectAll}>
              {selected.size === filteredContent.length
                ? "Снять выделение"
                : "Выбрать все"}
            </Button>
          </div>
        </div>

        {/* Content List */}
        {loading ? (
          <div style={{ textAlign: "center", padding: spacing.xl }}>
            Загрузка...
          </div>
        ) : filteredContent.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: spacing.xl,
              color: colors.textSecondary,
            }}
          >
            Нет доступного контента для публикации
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gap: spacing.md,
              maxHeight: "500px",
              overflow: "auto",
            }}
          >
            {filteredContent.map((item) => {
              const isExpanded = expandedText.has(item.id);
              const hasLongText =
                item.content_text && item.content_text.length > 150;

              return (
                <div
                  key={item.id}
                  style={{
                    border: `2px solid ${
                      selected.has(item.id) ? colors.primary[500] : colors.border
                    }`,
                    borderRadius: "8px",
                    padding: spacing.md,
                    backgroundColor: selected.has(item.id)
                      ? `${colors.primary[500]}10`
                      : "white",
                    transition: "all 0.2s",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      gap: spacing.md,
                      alignItems: "flex-start",
                    }}
                  >
                    {/* Preview */}
                    {item.content_type === "video" && item.file_path && (
                      <div
                        style={{
                          width: "120px",
                          height: "90px",
                          flexShrink: 0,
                          borderRadius: "6px",
                          overflow: "hidden",
                          backgroundColor: colors.gray[100],
                          position: "relative",
                        }}
                      >
                        <video
                          src={`${API_BASE_URL}/content/media/${item.file_path}`}
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                          }}
                        />
                        <div
                          style={{
                            position: "absolute",
                            top: "50%",
                            left: "50%",
                            transform: "translate(-50%, -50%)",
                            width: "30px",
                            height: "30px",
                            borderRadius: "50%",
                            backgroundColor: "rgba(0,0,0,0.6)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "white",
                            fontSize: "12px",
                          }}
                        >
                          ▶
                        </div>
                      </div>
                    )}
                    {item.content_type === "image" && item.file_path && (
                      <div
                        style={{
                          width: "120px",
                          height: "90px",
                          flexShrink: 0,
                          borderRadius: "6px",
                          overflow: "hidden",
                          backgroundColor: colors.gray[100],
                        }}
                      >
                        <img
                          src={`${API_BASE_URL}/content/media/${item.file_path}`}
                          alt="Preview"
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                          }}
                        />
                      </div>
                    )}
                    {item.content_type === "text" && (
                      <div
                        style={{
                          width: "120px",
                          height: "90px",
                          flexShrink: 0,
                          borderRadius: "6px",
                          backgroundColor: colors.gray[100],
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "36px",
                          color: colors.gray[500],
                        }}
                      >
                        📝
                      </div>
                    )}

                    {/* Content Info */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          display: "flex",
                          gap: spacing.sm,
                          marginBottom: spacing.xs,
                          flexWrap: "wrap",
                        }}
                      >
                        <Badge
                          variant={
                            item.content_type === "video"
                              ? "primary"
                              : item.content_type === "image"
                              ? "neutral"
                              : "success"
                          }
                        >
                          {item.content_type === "video"
                            ? "Видео"
                            : item.content_type === "image"
                            ? "Изображение"
                            : "Текст"}
                        </Badge>
                        <Badge variant="neutral">
                          {item.platform.toUpperCase()}
                        </Badge>
                      </div>

                      {/* Text Content */}
                      {item.content_text && (
                        <div>
                          <p
                            style={{
                              margin: 0,
                              fontSize: "14px",
                              color: colors.textSecondary,
                              whiteSpace: isExpanded ? "pre-wrap" : "normal",
                              wordBreak: "break-word",
                            }}
                          >
                            {isExpanded
                              ? item.content_text
                              : hasLongText
                              ? item.content_text.slice(0, 150) + "..."
                              : item.content_text}
                          </p>
                          {hasLongText && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleExpandText(item.id);
                              }}
                              style={{
                                marginTop: spacing.xs,
                                padding: "4px 8px",
                                fontSize: "12px",
                                color: colors.primary[500],
                                background: "none",
                                border: "none",
                                cursor: "pointer",
                                textDecoration: "underline",
                              }}
                            >
                              {isExpanded ? "Свернуть" : "Развернуть"}
                            </button>
                          )}
                        </div>
                      )}

                      <p
                        style={{
                          margin: `${spacing.xs} 0 0 0`,
                          fontSize: "12px",
                          color: colors.textSecondary,
                        }}
                      >
                        Создано:{" "}
                        {new Date(item.created_at).toLocaleDateString("ru-RU")}
                      </p>
                    </div>

                    {/* Checkbox */}
                    <div
                      onClick={() => toggleSelect(item.id)}
                      style={{
                        width: "24px",
                        height: "24px",
                        flexShrink: 0,
                        borderRadius: "4px",
                        border: `2px solid ${
                          selected.has(item.id)
                            ? colors.primary[500]
                            : colors.border
                        }`,
                        backgroundColor: selected.has(item.id)
                          ? colors.primary[500]
                          : colors.white,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "white",
                        fontSize: "16px",
                        cursor: "pointer",
                      }}
                    >
                      {selected.has(item.id) && "✓"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: spacing.lg,
            paddingTop: spacing.md,
            borderTop: `1px solid ${colors.border}`,
          }}
        >
          <div style={{ color: colors.textSecondary }}>
            Выбрано: {selected.size} из {filteredContent.length}
          </div>
          <div style={{ display: "flex", gap: spacing.md }}>
            <Button variant="ghost" onClick={onClose}>
              Отмена
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirm}
              disabled={selected.size === 0}
            >
              Продолжить ({selected.size})
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
