import React from "react";
import { colors, radius, shadows, spacing } from "../../theme";

export interface CardProps {
  title?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  padding?: "sm" | "md" | "lg" | "none";
  style?: React.CSSProperties;
  className?: string;
  onClick?: (e?: React.MouseEvent<HTMLDivElement>) => void;
}

export const Card: React.FC<CardProps> = ({
  title,
  actions,
  children,
  padding = "md",
  style,
  className,
  onClick,
}) => {
  const paddingMap = {
    none: 0,
    sm: spacing.sm,
    md: spacing.lg, // 24px
    lg: spacing.xl,
  };

  const cardStyle: React.CSSProperties = {
    backgroundColor: colors.background.card,
    borderRadius: radius.md,
    boxShadow: shadows.card,
    border: `1px solid ${colors.gray[200]}`,
    overflow: "hidden",
    cursor: onClick ? "pointer" : "default",
    width: "100%",
    boxSizing: "border-box",
    ...style,
  };

  return (
    <div className={className} style={cardStyle} onClick={onClick}>
      {(title || actions) && (
        <div
          style={{
            padding: `${spacing.md} ${spacing.lg}`,
            borderBottom: `1px solid ${colors.gray[100]}`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          {title && (
            <h3
              style={{
                margin: 0,
                fontSize: "16px",
                fontWeight: 600,
                color: colors.gray[900],
              }}
            >
              {title}
            </h3>
          )}
          {actions && <div>{actions}</div>}
        </div>
      )}
      <div style={{ padding: paddingMap[padding] }}>{children}</div>
    </div>
  );
};
