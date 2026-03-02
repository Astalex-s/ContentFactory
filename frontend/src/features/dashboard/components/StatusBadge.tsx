import React from "react";
import { Badge } from "../../../ui/components/Badge";

interface StatusBadgeProps {
  status: string;
  type: "content" | "publication";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type }) => {
  if (type === "content") {
    switch (status) {
      case "no_content":
        return <Badge variant="neutral">Нет контента</Badge>;
      case "text_ready":
        return <Badge variant="info">Текст готов</Badge>;
      case "image_ready":
        return <Badge variant="primary">Изображение готово</Badge>;
      case "video_ready":
        return <Badge variant="primary">Видео готово</Badge>;
      case "complete":
        return <Badge variant="success">Готово</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  } else {
    switch (status) {
      case "not_scheduled":
        return <Badge variant="neutral">Не запланировано</Badge>;
      case "scheduled":
        return <Badge variant="warning">Запланировано</Badge>;
      case "published":
        return <Badge variant="success">Опубликовано</Badge>;
      case "failed":
        return <Badge variant="danger">Ошибка</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  }
};
