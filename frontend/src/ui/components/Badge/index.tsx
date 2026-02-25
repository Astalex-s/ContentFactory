import React from "react";
import { colors, radius } from "../../theme";

export interface BadgeProps {
  children: React.ReactNode;
  variant?: "success" | "warning" | "danger" | "info" | "neutral" | "primary";
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = "neutral" }) => {
  const styles = {
    success: { bg: "#DCFCE7", color: "#166534" },
    warning: { bg: "#FEF3C7", color: "#92400E" },
    danger: { bg: "#FEE2E2", color: "#991B1B" },
    info: { bg: "#DBEAFE", color: "#1E40AF" },
    neutral: { bg: colors.gray[100], color: colors.gray[700] },
    primary: { bg: colors.primary[100], color: colors.primary[600] },
  };

  const currentStyle = styles[variant];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: radius.sm,
        fontSize: "12px",
        fontWeight: 500,
        backgroundColor: currentStyle.bg,
        color: currentStyle.color,
        lineHeight: 1.5,
      }}
    >
      {children}
    </span>
  );
};
