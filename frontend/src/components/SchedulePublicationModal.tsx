import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Button } from "../ui/components/Button";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { publishService, PublicationScheduleItem } from "../services/publishService";
import { socialService, SocialAccount } from "../services/social";
import { contentService, GeneratedContent } from "../services/content";
import { productsService } from "../services/products";
import { contentApi } from "../features/content";
import { apiBaseURL } from "../services/api";

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

const UUID_REGEX =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function isValidUuid(s: unknown): s is string {
  return typeof s === "string" && s.length > 0 && UUID_REGEX.test(s);
}

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
  const [loadingMedia, setLoadingMedia] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generateTitleLoading, setGenerateTitleLoading] = useState<number | null>(null);
  const [openMediaDropdown, setOpenMediaDropdown] = useState<number | null>(null);
  const [openTextDropdown, setOpenTextDropdown] = useState<number | null>(null);
  const [youtubePrivacy, setYoutubePrivacy] = useState<"private" | "public" | "unlisted">("private");
  const mediaDropdownRef = useRef<HTMLDivElement>(null);
  const textDropdownRef = useRef<HTMLDivElement>(null);
  const prevOpenRef = useRef(false);
  const selectedIdsRef = useRef("");

  const getMediaUrl = (filePath: string) =>
    `${apiBaseURL}/content/media/${filePath}`;

  // Инициализация только при открытии модалки или смене selectedContent.
  // selectedContent={[]} создаёт новый массив при каждом рендере родителя — не сбрасывать schedules.
  useEffect(() => {
    if (!isOpen) {
      prevOpenRef.current = false;
      return;
    }
    loadAccounts();
    loadVideosAndText();
    const selectedIds = selectedContent
      .map((c) => c?.id ?? "")
      .filter(Boolean)
      .sort()
      .join(",");
    const justOpened = !prevOpenRef.current;
    const contentChanged = selectedIdsRef.current !== selectedIds;
    if (justOpened || contentChanged) {
      initializeSchedules();
      prevOpenRef.current = true;
      selectedIdsRef.current = selectedIds;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, selectedContent.map((c) => c?.id).filter(Boolean).join(",")]);

  useEffect(() => {
    if (!isOpen || (openMediaDropdown === null && openTextDropdown === null)) return;
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (openMediaDropdown !== null && mediaDropdownRef.current && !mediaDropdownRef.current.contains(target)) {
        setOpenMediaDropdown(null);
      }
      if (openTextDropdown !== null && textDropdownRef.current && !textDropdownRef.current.contains(target)) {
        setOpenTextDropdown(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, openMediaDropdown, openTextDropdown]);

  // По умолчанию: заголовок = описание товара (первая строка), когда загрузятся данные
  useEffect(() => {
    if (!isOpen || Object.keys(productData).length === 0) return;
    setSchedules((prev) =>
      prev.map((s) => {
        if (s.title || !s.productId) return s;
        const prod = productData[s.productId];
        if (!prod) return s;
        const defaultTitle =
          prod.description?.split(/\r?\n/)[0]?.trim().slice(0, 100) || prod.name;
        return { ...s, title: defaultTitle };
      })
    );
  }, [productData, isOpen]);

  const loadAccounts = async () => {
    try {
      const data = await socialService.getAccounts();
      const list = Array.isArray(data) ? data : [];
      setAccounts(list.filter((a) => a && isValidUuid(a.id)));
    } catch (err) {
      console.error("Failed to load accounts:", err);
      setError("Не удалось загрузить подключённые аккаунты");
      setAccounts([]);
    }
  };

  const loadVideosAndText = async () => {
    setLoadingMedia(true);
    setError(null);
    try {
      const data = await contentService.getAllContent(1, 100);
      const items = Array.isArray(data?.items) ? data.items : [];
      const mediaItems = items.filter(
        (item) =>
          item &&
          typeof item.id === "string" &&
          isValidUuid(item.id) &&
          (item.content_type === "video" || item.content_type === "image") &&
          (String(item.status).toLowerCase() === "ready" ||
            String(item.status).toLowerCase() === "draft")
      );
      setVideos(mediaItems);

      const productIds = [
        ...new Set(
          [
            ...mediaItems.map((c) => (c.product_id != null ? String(c.product_id) : "")),
            ...selectedContent.map((c) => (c.product_id != null ? String(c.product_id) : "")),
          ].filter((x) => x && x !== "undefined" && x !== "null")
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
    } catch (err) {
      console.error("Failed to load media and products:", err);
      setVideos([]);
      setProductTextContent({});
      setProductData({});
      setError("Не удалось загрузить видео/изображения и данные товаров");
    } finally {
      setLoadingMedia(false);
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
            const productId = content.product_id != null ? String(content.product_id) : "";
            return {
              content_id: content.id ?? "",
              platform: "",
              account_id: "",
              scheduled_at: scheduledTime.toISOString().slice(0, 16),
              title: "",
              description: "",
              descriptionContentId: "",
              productId,
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
        if (field === "platform") {
          updated.account_id = "";
        }
        if (field === "content_id" && value) {
          const media = videos.find((v) => v.id === value);
          if (media) {
            updated.productId = media.product_id != null ? String(media.product_id) : "";
            updated.contentTitle = `${media.content_type === "image" ? "Изображение" : "Видео"} ${media.platform} • вариант ${media.content_variant ?? 1}`;
            if (!updated.descriptionContentId) {
              updated.descriptionContentId = PRODUCT_DESCRIPTION_ID;
            }
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
        setError("Выберите видео или изображение для каждой публикации");
        return;
      }
      if (!isValidUuid(schedule.content_id)) {
        setError("Некорректный ID контента. Обновите страницу и попробуйте снова.");
        return;
      }
      const selectedMedia = videos.find((v) => v.id === schedule.content_id);
      if (selectedMedia?.content_type === "image") {
        setError("Для публикации на платформы поддерживаются только видео. Выберите видео.");
        return;
      }
      if (!schedule.platform || !schedule.account_id) {
        setError("Выберите платформу и аккаунт для всех публикаций");
        return;
      }
      if (!isValidUuid(schedule.account_id)) {
        setError("Некорректный ID аккаунта. Переподключите канал в настройках.");
        return;
      }
    }

    setLoading(true);
    try {
      const payload = schedules.map((s) => {
        let description = s.description;
        const productId = s.productId && String(s.productId) !== "undefined" ? s.productId : "";
        if (s.descriptionContentId === PRODUCT_NAME_ID && productId && productData[productId]) {
          description = productData[productId].name;
        } else if (s.descriptionContentId === PRODUCT_DESCRIPTION_ID && productId && productData[productId]) {
          description = productData[productId].description || "";
        } else if (s.descriptionContentId && productId && productTextContent[productId]) {
          const textItem = productTextContent[productId].find(
            (t) => t.id === s.descriptionContentId
          );
          description = textItem?.content_text || "";
        }
        const contentId = (typeof s.content_id === "string" ? s.content_id : "").trim();
        const accountId = (typeof s.account_id === "string" ? s.account_id : "").trim();
        const platform = String(s.platform ?? "").trim();
        const scheduledAt = s.scheduled_at ? String(s.scheduled_at).trim() : "";
        if (!contentId || contentId === "undefined" || contentId === "null" || !isValidUuid(contentId)) {
          throw new Error("Некорректный ID контента. Выберите видео заново.");
        }
        if (!accountId || accountId === "undefined" || accountId === "null" || !isValidUuid(accountId)) {
          throw new Error("Некорректный ID аккаунта. Выберите аккаунт заново.");
        }
        if (!platform || !["youtube", "vk", "tiktok"].includes(platform)) {
          throw new Error("Выберите платформу (YouTube, VK или TikTok).");
        }
        if (!scheduledAt || isNaN(new Date(scheduledAt).getTime())) {
          throw new Error("Укажите дату и время публикации.");
        }
        return {
          content_id: contentId,
          platform,
          account_id: accountId,
          scheduled_at: new Date(scheduledAt).toISOString(),
          title: s.title?.trim() || undefined,
          description: description?.trim() || undefined,
          privacy_status: platform === "youtube" ? youtubePrivacy : "private",
        };
      });
      await publishService.bulkSchedulePublications({ publications: payload });
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string | unknown[] } }; message?: string };
      const detail = ax?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? (detail as { msg?: string }[])
                .map((e) => e?.msg)
                .filter((m): m is string => Boolean(m))
                .join("; ") || "Ошибка валидации"
            : ax?.message || "Не удалось запланировать публикации";
      setError(msg);
      console.error("Schedule publication error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const platformAccounts = (platform: string) =>
    Array.isArray(accounts) ? accounts.filter((a) => a.platform === platform) : [];

  const modalContent = (
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
        zIndex: 9999,
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

        {loadingMedia && (
          <Alert type="info">Загрузка видео, изображений и данных товаров…</Alert>
        )}
        {error && <Alert type="error">{error}</Alert>}

        {accounts.some((a) => a.platform === "youtube") && (
          <div style={{ marginTop: spacing.md, marginBottom: spacing.sm }}>
            <label
              style={{
                display: "block",
                marginBottom: spacing.xs,
                fontWeight: 500,
              }}
            >
              Доступ к видео (YouTube)
            </label>
            <select
              value={youtubePrivacy}
              onChange={(e) =>
                setYoutubePrivacy(e.target.value as "private" | "public" | "unlisted")
              }
              style={{
                padding: spacing.sm,
                borderRadius: "6px",
                border: `1px solid ${colors.border}`,
                minWidth: 200,
              }}
            >
              <option value="private">Приватный (только вы)</option>
              <option value="unlisted">По ссылке (не в поиске)</option>
              <option value="public">Публичный (без ограничений)</option>
            </select>
          </div>
        )}

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
                    Видео или изображение *
                  </label>
                  <div
                    ref={openMediaDropdown === index ? mediaDropdownRef : undefined}
                    style={{ position: "relative", width: "100%" }}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        setOpenTextDropdown(null);
                        setOpenMediaDropdown(openMediaDropdown === index ? null : index);
                      }}
                      style={{
                        width: "100%",
                        padding: spacing.sm,
                        borderRadius: "6px",
                        border: `1px solid ${colors.border}`,
                        backgroundColor: colors.white,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: spacing.sm,
                        textAlign: "left",
                        minHeight: 52,
                      }}
                    >
                      {schedule.content_id ? (
                        (() => {
                          const sel = videos.find((v) => v.id === schedule.content_id);
                          if (!sel) return <span>Выберите контент</span>;
                          return (
                            <>
                              {sel.file_path ? (
                                sel.content_type === "video" ? (
                                  <video
                                    src={getMediaUrl(sel.file_path)}
                                    style={{
                                      width: 64,
                                      height: 36,
                                      objectFit: "cover",
                                      borderRadius: 4,
                                      flexShrink: 0,
                                    }}
                                    muted
                                    preload="metadata"
                                  />
                                ) : (
                                  <img
                                    src={getMediaUrl(sel.file_path)}
                                    alt=""
                                    style={{
                                      width: 64,
                                      height: 36,
                                      objectFit: "cover",
                                      borderRadius: 4,
                                      flexShrink: 0,
                                    }}
                                  />
                                )
                              ) : (
                                <div
                                  style={{
                                    width: 64,
                                    height: 36,
                                    backgroundColor: colors.gray[100],
                                    borderRadius: 4,
                                    flexShrink: 0,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    fontSize: 20,
                                  }}
                                >
                                  {sel.content_type === "image" ? "🖼" : "▶"}
                                </div>
                              )}
                              <span style={{ flex: 1, fontSize: 14 }}>
                                {sel.content_type === "image" ? "Изображение" : "Видео"} •{" "}
                                {sel.platform} • вариант {sel.content_variant ?? 1}
                              </span>
                            </>
                          );
                        })()
                      ) : (
                        <span style={{ color: colors.textSecondary }}>
                          {videos.length === 0
                            ? "Нет видео/изображений в базе"
                            : "Выберите видео или изображение"}
                        </span>
                      )}
                      <span style={{ fontSize: 12 }}>▼</span>
                    </button>
                    {openMediaDropdown === index && (
                      <div
                        style={{
                          position: "absolute",
                          top: "100%",
                          left: 0,
                          right: 0,
                          marginTop: 4,
                          maxHeight: 280,
                          overflowY: "auto",
                          backgroundColor: colors.white,
                          border: `1px solid ${colors.border}`,
                          borderRadius: 6,
                          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                          zIndex: 100,
                        }}
                      >
                        {videos
                          .filter((v) => v.id && isValidUuid(v.id))
                          .map((v) => (
                            <button
                              key={v.id}
                              type="button"
                              onClick={() => {
                                const id = v.id != null ? String(v.id) : "";
                                if (id && isValidUuid(id)) {
                                  updateSchedule(index, "content_id", id);
                                  setOpenMediaDropdown(null);
                                }
                              }}
                              style={{
                                width: "100%",
                                padding: spacing.sm,
                                border: "none",
                                backgroundColor: schedule.content_id === v.id ? colors.primary[100] : "transparent",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                gap: spacing.sm,
                                textAlign: "left",
                                borderBottom: `1px solid ${colors.border}`,
                              }}
                            >
                              {v.file_path ? (
                                v.content_type === "video" ? (
                                  <video
                                    src={getMediaUrl(v.file_path)}
                                    style={{
                                      width: 80,
                                      height: 45,
                                      objectFit: "cover",
                                      borderRadius: 4,
                                      flexShrink: 0,
                                    }}
                                    muted
                                    preload="metadata"
                                  />
                                ) : (
                                  <img
                                    src={getMediaUrl(v.file_path)}
                                    alt=""
                                    style={{
                                      width: 80,
                                      height: 45,
                                      objectFit: "cover",
                                      borderRadius: 4,
                                      flexShrink: 0,
                                    }}
                                  />
                                )
                              ) : (
                                <div
                                  style={{
                                    width: 80,
                                    height: 45,
                                    backgroundColor: colors.gray[100],
                                    borderRadius: 4,
                                    flexShrink: 0,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    fontSize: 24,
                                  }}
                                >
                                  {v.content_type === "image" ? "🖼" : "▶"}
                                </div>
                              )}
                              <span style={{ flex: 1, fontSize: 13 }}>
                                {v.content_type === "image" ? "Изображение" : "Видео"} •{" "}
                                {v.platform} • вариант {v.content_variant ?? 1}
                              </span>
                            </button>
                          ))}
                      </div>
                    )}
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
                      onChange={(e) => {
                        const val = (e.target.value ?? "").trim();
                        const sanitized =
                          val === "undefined" || val === "null" ? "" : val;
                        updateSchedule(index, "account_id", sanitized);
                      }}
                      style={{
                        width: "100%",
                        padding: spacing.sm,
                        borderRadius: "6px",
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      <option value="">Выберите аккаунт</option>
                      {platformAccounts(schedule.platform)
                        .filter((acc) => acc.id && isValidUuid(acc.id))
                        .map((acc) => (
                          <option key={acc.id} value={String(acc.id)}>
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
                  <div style={{ display: "flex", flexDirection: "column", gap: spacing.sm }}>
                    <select
                      value=""
                      onChange={(e) => {
                        const val = e.target.value;
                        if (!val || !schedule.productId) return;
                        const prod = productData[schedule.productId];
                        if (!prod) return;
                        if (val === PRODUCT_NAME_ID) {
                          updateSchedule(index, "title", prod.name);
                        } else if (val === PRODUCT_DESCRIPTION_ID && prod.description) {
                          updateSchedule(
                            index,
                            "title",
                            prod.description.split(/\r?\n/)[0]?.trim().slice(0, 100) || prod.name
                          );
                        }
                      }}
                      style={{
                        width: "100%",
                        padding: spacing.sm,
                        borderRadius: "6px",
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      <option value="">Выберите заголовок из списка</option>
                      {schedule.productId && productData[schedule.productId] && (
                        <>
                          <option value={PRODUCT_NAME_ID}>
                            Заголовок товара: {productData[schedule.productId].name.slice(0, 40)}
                            {productData[schedule.productId].name.length > 40 ? "…" : ""}
                          </option>
                          {productData[schedule.productId].description && (
                            <option value={PRODUCT_DESCRIPTION_ID}>
                              Описание товара (первая строка)
                            </option>
                          )}
                        </>
                      )}
                    </select>
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
                  <div
                    ref={openTextDropdown === index ? textDropdownRef : undefined}
                    style={{ position: "relative", width: "100%" }}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        setOpenMediaDropdown(null);
                        setOpenTextDropdown(openTextDropdown === index ? null : index);
                      }}
                      style={{
                        width: "100%",
                        padding: spacing.sm,
                        borderRadius: "6px",
                        border: `1px solid ${colors.border}`,
                        backgroundColor: colors.white,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: spacing.sm,
                        textAlign: "left",
                        minHeight: 52,
                      }}
                    >
                      <span
                        style={{
                          flex: 1,
                          fontSize: 13,
                          whiteSpace: "pre-wrap",
                          wordBreak: "break-word",
                          maxHeight: 60,
                          overflow: "hidden",
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical" as const,
                        }}
                      >
                        {schedule.descriptionContentId ? (
                          (() => {
                            const prod = schedule.productId ? productData[schedule.productId] : undefined;
                            if (schedule.descriptionContentId === PRODUCT_NAME_ID && prod) {
                              return prod.name;
                            }
                            if (schedule.descriptionContentId === PRODUCT_DESCRIPTION_ID && prod?.description) {
                              return prod.description;
                            }
                            const textItem = (productTextContent[schedule.productId] || []).find(
                              (t) => t.id === schedule.descriptionContentId
                            );
                            return textItem?.content_text || "—";
                          })()
                        ) : (
                          <span style={{ color: colors.textSecondary }}>— Пусто —</span>
                        )}
                      </span>
                      <span style={{ fontSize: 12, flexShrink: 0 }}>▼</span>
                    </button>
                    {openTextDropdown === index && (
                      <div
                        style={{
                          position: "absolute",
                          top: "100%",
                          left: 0,
                          right: 0,
                          marginTop: 4,
                          maxHeight: 240,
                          overflowY: "auto",
                          backgroundColor: colors.white,
                          border: `1px solid ${colors.border}`,
                          borderRadius: 6,
                          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                          zIndex: 100,
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => {
                            updateSchedule(index, "descriptionContentId", "");
                            setOpenTextDropdown(null);
                          }}
                          style={{
                            width: "100%",
                            padding: spacing.sm,
                            border: "none",
                            borderBottom: `1px solid ${colors.border}`,
                            backgroundColor: !schedule.descriptionContentId ? colors.primary[100] : "transparent",
                            cursor: "pointer",
                            textAlign: "left",
                            fontSize: 13,
                            color: colors.textSecondary,
                          }}
                        >
                          — Пусто —
                        </button>
                        {schedule.productId && productData[schedule.productId] && (
                          <>
                            <button
                              type="button"
                              onClick={() => {
                                updateSchedule(index, "descriptionContentId", PRODUCT_NAME_ID);
                                setOpenTextDropdown(null);
                              }}
                              style={{
                                width: "100%",
                                padding: spacing.sm,
                                border: "none",
                                borderBottom: `1px solid ${colors.border}`,
                                backgroundColor: schedule.descriptionContentId === PRODUCT_NAME_ID ? colors.primary[100] : "transparent",
                                cursor: "pointer",
                                textAlign: "left",
                                fontSize: 12,
                              }}
                            >
                              <div style={{ fontWeight: 500, marginBottom: 4 }}>Заголовок товара</div>
                              <div
                                style={{
                                  color: colors.textSecondary,
                                  whiteSpace: "pre-wrap",
                                  wordBreak: "break-word",
                                  maxHeight: 48,
                                  overflow: "hidden",
                                  display: "-webkit-box",
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: "vertical" as const,
                                }}
                              >
                                {productData[schedule.productId].name}
                              </div>
                            </button>
                            {productData[schedule.productId].description && (
                              <button
                                type="button"
                                onClick={() => {
                                  updateSchedule(index, "descriptionContentId", PRODUCT_DESCRIPTION_ID);
                                  setOpenTextDropdown(null);
                                }}
                                style={{
                                  width: "100%",
                                  padding: spacing.sm,
                                  border: "none",
                                  borderBottom: `1px solid ${colors.border}`,
                                  backgroundColor: schedule.descriptionContentId === PRODUCT_DESCRIPTION_ID ? colors.primary[100] : "transparent",
                                  cursor: "pointer",
                                  textAlign: "left",
                                  fontSize: 12,
                                }}
                              >
                                <div style={{ fontWeight: 500, marginBottom: 4 }}>Описание товара</div>
                                <div
                                  style={{
                                    color: colors.textSecondary,
                                    whiteSpace: "pre-wrap",
                                    wordBreak: "break-word",
                                    maxHeight: 48,
                                    overflow: "hidden",
                                    display: "-webkit-box",
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: "vertical" as const,
                                  }}
                                >
                                  {productData[schedule.productId].description}
                                </div>
                              </button>
                            )}
                          </>
                        )}
                        {(productTextContent[schedule.productId] || []).map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => {
                              updateSchedule(index, "descriptionContentId", item.id);
                              setOpenTextDropdown(null);
                            }}
                            style={{
                              width: "100%",
                              padding: spacing.sm,
                              border: "none",
                              borderBottom: `1px solid ${colors.border}`,
                              backgroundColor: schedule.descriptionContentId === item.id ? colors.primary[100] : "transparent",
                              cursor: "pointer",
                              textAlign: "left",
                              fontSize: 12,
                            }}
                          >
                            <div style={{ fontWeight: 500, marginBottom: 4 }}>
                              {contentTextTypeLabels[item.content_text_type ?? ""] ?? item.content_text_type} •{" "}
                              {item.platform} • вариант {item.content_variant ?? 1}
                            </div>
                            {item.content_text && (
                              <div
                                style={{
                                  color: colors.textSecondary,
                                  whiteSpace: "pre-wrap",
                                  wordBreak: "break-word",
                                  maxHeight: 48,
                                  overflow: "hidden",
                                  display: "-webkit-box",
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: "vertical" as const,
                                }}
                              >
                                {item.content_text}
                              </div>
                            )}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
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
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={loading}
          >
            Отмена
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? "Планирование..." : "Запланировать"}
          </Button>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
