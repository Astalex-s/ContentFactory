import React from "react";
import { colors, spacing } from "../../theme";

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  width?: string | number;
  align?: "left" | "center" | "right";
}

export interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  isLoading?: boolean;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  actions?: (item: T) => React.ReactNode;
}

export function Table<T extends { id: string | number }>({
  data,
  columns,
  isLoading,
  emptyMessage = "No data available",
  onRowClick,
  actions,
}: TableProps<T>) {
  if (isLoading) {
    return <div style={{ padding: spacing.lg, textAlign: "center" }}>Loading...</div>;
  }

  if (data.length === 0) {
    return (
      <div
        style={{
          padding: spacing.xl,
          textAlign: "center",
          color: colors.gray[500],
          backgroundColor: colors.gray[50],
          borderRadius: 8,
        }}
      >
        {emptyMessage}
      </div>
    );
  }

  return (
    <div style={{ overflowX: "auto", width: "100%" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "max-content" }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${colors.gray[200]}` }}>
            {columns.map((col) => (
              <th
                key={col.key}
                style={{
                  padding: spacing.md,
                  textAlign: col.align || "left",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: colors.gray[500],
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  width: col.width,
                  whiteSpace: "nowrap",
                }}
              >
                {col.header}
              </th>
            ))}
            {actions && (
              <th
                style={{
                  padding: spacing.md,
                  textAlign: "right",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: colors.gray[500],
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  whiteSpace: "nowrap",
                }}
              >
                Действия
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr
              key={item.id}
              onClick={() => onRowClick?.(item)}
              style={{
                borderBottom: `1px solid ${colors.gray[100]}`,
                cursor: onRowClick ? "pointer" : "default",
                transition: "background-color 0.1s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = colors.gray[50])
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = "transparent")
              }
            >
              {columns.map((col) => (
                <td
                  key={`${item.id}-${col.key}`}
                  style={{
                    padding: spacing.md,
                    textAlign: col.align || "left",
                    fontSize: "14px",
                    color: colors.gray[900],
                  }}
                >
                  {col.render ? col.render(item) : (item as any)[col.key]}
                </td>
              ))}
              {actions && (
                <td
                  style={{
                    padding: spacing.md,
                    textAlign: "right",
                    fontSize: "14px",
                    color: colors.gray[900],
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {actions(item)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
