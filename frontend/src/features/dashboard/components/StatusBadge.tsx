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
        return <Badge variant="neutral">No Content</Badge>;
      case "text_ready":
        return <Badge variant="info">Text Ready</Badge>;
      case "image_ready":
        return <Badge variant="primary">Image Ready</Badge>;
      case "video_ready":
        return <Badge variant="primary">Video Ready</Badge>;
      case "complete":
        return <Badge variant="success">Complete</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  } else {
    switch (status) {
      case "not_scheduled":
        return <Badge variant="neutral">Not Scheduled</Badge>;
      case "scheduled":
        return <Badge variant="warning">Scheduled</Badge>;
      case "published":
        return <Badge variant="success">Published</Badge>;
      case "failed":
        return <Badge variant="danger">Failed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  }
};
