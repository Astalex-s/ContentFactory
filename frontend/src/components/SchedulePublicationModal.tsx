import { useState, useEffect } from "react";
import { Button } from "../ui/components/Button";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { publishService, PublicationScheduleItem } from "../services/publishService";
import { socialService, SocialAccount } from "../services/social";
import { contentService, GeneratedContent } from "../services/content";
import { productsService } from "../services/products";
import { contentApi } from "../features/content";

interface SchedulePublicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: GeneratedContent[];
  onSuccess: () => void;
}

const contentTextTypeLabels: Record<string, string> = {
  short_post: "Короткий пост",
  video_description: "Описание видео",
  cta: "Призыв к действию",
  all: "Все",
};

/** Виртуальные ID для текста из карточки товара (когда нет сгенерированных постов) */
const PRODUCT_NAME_ID = "__product_name__";
const PRODUCT_DESCRIPTION_ID = "__product_description__";

interface ScheduleItem extends PublicationScheduleItem {
  contentTitle: string;
  productId: string;
  descriptionContentId: string;
}

export function SchedulePublicationModal({
  isOpen,
  onClose,
  selectedContent,
  onSuccess,
}: SchedulePublicationModalProps) {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [videos, setVideos] = useState<GeneratedContent[]>([]);
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [productTextContent, setProductTextContent] = useState<
    Record<string, GeneratedContent[]>
  >({});
  const [productData, setProductData] = useState<
    Record<string, { name: string; description: string | null }>
  >({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generateTitleLoading, setGenerateTitleLoading] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadAccounts();
      loadVideosAndText();
      initializeSchedules();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, selectedContent]);

  // Предзаполнить заголовок названием товара, когда загрузятся данные
  useEffect(() => {
    if (!isOpen || Object.keys(productData).length === 0) return;
    setSchedules((prev) =>
      prev.map((s) => {
        if (s.title || !s.productId) return s;
        const prod = productData[s.productId];
        if (!prod?.name) return s;
        return { ...s, title: prod.name };
      })
    );
  }, [productData, isOpen]);

  const loadAccounts = async () => {
    try {
      const data = await socialService.getAccounts();
      setAccounts(data);
    } catch (err) {
      console.error("Failed to load accounts:", err);
      setError("Не удалось загрузить подключённые аккаунты");
    }
  };

  const loadVideosAndText = async () => {
    try {
      const data = await contentService.getAllContent(1, 200);
      const videoItems = data.items.filter(
        (item) => item.content_type === "video" && item.status === "ready"
      );
      setVideos(videoItems);

      const productIds = [
        ...new Set(
          [
            ...videoItems.map((c) => String(c.product_id)),
            ...selectedContent.map((c) => String(c.product_id)),
          ].filter(Boolean)
        ),
      ];
      const map: Record<string, GeneratedContent[]> = {};
      const productMap: Record<string, { name: string; description: string | null }> = {};
      await Promise.all(
        productIds.map(async (productId) => {
          try {
            const [prodContent, product] = await Promise.all([
              contentService.getContentByProduct(productId, 1, 100),
              productsService.getProduct(productId),
            ]);
            const textItems = (prodContent?.items ?? []).filter(
              (item) => item.content_type === "text" && item.content_text
            );
            map[productId] = textItems;
            productMap[productId] = {
              name: product?.name ?? "Товар",
              description: product?.description ?? null,
            };
          } catch {
            map[productId] = [];
            productMap[productId] = { name: "Товар", description: null };
          }
        })
      );
      setProductTextContent(map);
      setProductData(productMap);
    } catch {
      setVideos([]);
      setProductTextContent({});
      setProductData({});
    }
  };

  const initializeSchedules = () => {
    const now = new Date();
    const items =
      selectedContent.length > 0
        ? selectedContent.map((content, index) => {
            const scheduledTime = new Date(
              now.getTime() + (index + 1) * 60 * 60 * 1000
            );
            return {
              content_id: content.id,
              platform: "",
              account_id: "",
              scheduled_at: scheduledTime.toISOString().slice(0, 16),
              title: "",
              description: "",
              descriptionContentId: "",
              productId: String(content.product_id),
              contentTitle: `Видео ${content.platform} • вариант ${content.content_variant ?? 1}`,
            };
          })
        : [
            {
              content_id: "",
              platform: "",
              account_id: "",
              scheduled_at: now.toISOString().slice(0, 16),
              title: "",
              description: "",
              descriptionContentId: "",
              productId: "",
              contentTitle: "",
            },
          ];
    setSchedules(items);
  };

  const addSchedule = () => {
    const now = new Date();
    const lastTime =
      schedules.length > 0 ? new Date(schedules[schedules.length - 1].scheduled_at) : now;
    const nextTime = new Date(lastTime.getTime() + 60 * 60 * 1000);
    setSchedules((prev) => [
      ...prev,
      {
        content_id: "",
        platform: "",
        account_id: "",
        scheduled_at: nextTime.toISOString().slice(0, 16),
        title: "",
        description: "",
        descriptionContentId: "",
        productId: "",
        contentTitle: "",
      },
    ]);
  };

  const removeSchedule = (index: number) => {
    if (schedules.length <= 1) return;
    setSchedules((prev) => prev.filter((_, i) => i !== index));
  };

  const updateSchedule = (index: number, field: keyof ScheduleItem, value: string) => {
    setSchedules((prev) =>
      prev.map((item, i) => {
        if (i !== index) return item;
        const updated = { ...item, [field]: value };
        if (field === "content_id" && value) {
          const video = videos.find((v) => v.id === value);
          if (video) {
            updated.productId = String(video.product_id);
            updated.contentTitle = `Видео ${video.platform} • вариант ${video.content_variant ?? 1}`;
          }
        }
        return updated;
      })
    );
  };

  const handleSubmit = async () => {
    setError(null);

    for (const schedule of schedules) {
      if (!schedule.content_id) {
        setError("Выберите видео для каждой публикации");
        return;
      }
      if (!schedule.platform || !schedule.account_id) {
        setError("Выберите платформу и аккаунт для всех публикаций");
        return;
      }
    }

    setLoading(true);
    try {
      await publishService.bulkSchedulePublications({
        publications: schedules.map((s) => {
          let description = s.description;
          if (s.descriptionContentId === PRODUCT_NAME_ID && productData[s.productId]) {
            description = productData[s.productId].name;
          } else if (s.descriptionContentId === PRODUCT_DESCRIPTION_ID && productData[s.productId]) {
            description = productData[s.productId].description || "";
          } else if (s.descriptionContentId && productTextContent[s.productId]) {
            const textItem = productTextContent[s.productId].find(
              (t) => t.id === s.descriptionContentId
            );
            description = textItem?.content_text || "";
          }
          return {
            content_id: s.content_id,
            platform: s.platform,
            account_id: s.account_id,
            scheduled_at: new Date(s.scheduled_at).toISOString(),
            title: s.title || undefined,
            description: description || undefined,
          };
        }),
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
          Платформа, дата/время, видео и текст поста для каждой публикации
        </p>

        {error && <Alert type="error">{error}</Alert>}

        <div style={{ marginTop: spacing.lg }}>
          {schedules.map((schedule, index) => (
            <div
              key={`${index}-${schedule.content_id}`}
              style={{
                border: `1px solid ${colors.border}`,
                borderRadius: "8px",
                padding: spacing.md,
                marginBottom: spacing.md,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: spacing.sm,
                }}
              >
                <h4 style={{ margin: 0 }}>
                  {schedule.contentTitle || `Публикация ${index + 1}`}
                </h4>
                {schedules.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeSchedule(index)}
                    style={{ color: colors.danger }}
                  >
                    Удалить
                  </Button>
                )}
              </div>

              <div style={{ display: "grid", gap: spacing.md }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      marginBottom: spacing.xs,
                      fontWeight: 500,
                    }}
                  >
                    Видео ролик *
                  </label>
                  <select
                    value={schedule.content_id}
                    onChange={(e) =>
                      updateSchedule(index, "content_id", e.target.value)
                    }
                    style={{
                      width: "100%",
                      padding: spacing.sm,
                      borderRadius: "6px",
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <option value="">Выберите видео</option>
                    {videos.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.platform} • вариант {v.content_variant ?? 1}
                      </option>
                    ))}
                  </select>
                </div>

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
                  <div style={{ display: "flex", gap: spacing.sm, alignItems: "center" }}>
                    <input
                      type="text"
                      value={schedule.title}
                      onChange={(e) =>
                        updateSchedule(index, "title", e.target.value)
                      }
                      placeholder="Название товара или сгенерированный заголовок"
                      maxLength={100}
                      style={{
                        flex: 1,
                        padding: spacing.sm,
                        borderRadius: "6px",
                        border: `1px solid ${colors.border}`,
                      }}
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={async () => {
                        if (!schedule.productId) return;
                        setGenerateTitleLoading(index);
                        setError(null);
                        try {
                          const generated = await contentApi.generateVideoTitle(schedule.productId);
                          updateSchedule(index, "title", generated);
                        } catch {
                          setError("Не удалось сгенерировать заголовок");
                        } finally {
                          setGenerateTitleLoading(null);
                        }
                      }}
                      disabled={!schedule.productId || generateTitleLoading !== null}
                    >
                      {generateTitleLoading === index ? "…" : "Сгенерировать"}
                    </Button>
                  </div>
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      marginBottom: spacing.xs,
                      fontWeight: 500,
                    }}
                  >
                    Текст поста (описание)
                  </label>
                  <select
                    value={schedule.descriptionContentId}
                    onChange={(e) =>
                      updateSchedule(index, "descriptionContentId", e.target.value)
                    }
                    style={{
                      width: "100%",
                      padding: spacing.sm,
                      borderRadius: "6px",
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <option value="">— Пусто —</option>
                    {schedule.productId && productData[schedule.productId] && (
                      <>
                        <option value={PRODUCT_NAME_ID}>
                          Заголовок товара: {productData[schedule.productId].name.slice(0, 40)}
                          {productData[schedule.productId].name.length > 40 ? "…" : ""}
                        </option>
                        {productData[schedule.productId].description && (
                          <option value={PRODUCT_DESCRIPTION_ID}>
                            Описание товара
                          </option>
                        )}
                      </>
                    )}
                    {(productTextContent[schedule.productId] || []).map(
                      (item) => (
                        <option key={item.id} value={item.id}>
                          {contentTextTypeLabels[item.content_text_type ?? ""] ??
                            item.content_text_type}{" "}
                          • {item.platform} • вариант{" "}
                          {item.content_variant ?? 1}
                        </option>
                      )
                    )}
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>

        <Button
          variant="secondary"
          onClick={addSchedule}
          style={{ marginTop: spacing.md }}
        >
          + Добавить публикацию
        </Button>

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
