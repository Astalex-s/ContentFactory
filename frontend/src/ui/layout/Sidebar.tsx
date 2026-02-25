import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { colors, spacing } from "../theme";

const navItems = [
  { path: "/dashboard", label: "Обзор" },
  { path: "/products", label: "Товары" },
  { path: "/content", label: "Контент" },
  { path: "/publishing", label: "Публикации" },
  { path: "/analytics", label: "Аналитика" },
  { path: "/creators", label: "Соцсети" },
  { path: "/settings", label: "Настройки" },
];

export const Sidebar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: "none",
          position: "fixed",
          top: spacing.md,
          left: spacing.md,
          zIndex: 20,
          padding: spacing.sm,
          backgroundColor: colors.white,
          border: `1px solid ${colors.gray[200]}`,
          borderRadius: 6,
          cursor: "pointer",
        }}
        className="mobile-menu-btn"
      >
        ☰
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          style={{
            display: "none",
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            zIndex: 11,
          }}
          className="mobile-overlay"
        />
      )}

      <aside
        style={{
          width: "240px",
          height: "100vh",
          backgroundColor: colors.primary[600],
          borderRight: "none",
          display: "flex",
          flexDirection: "column",
          position: "fixed",
          top: 0,
          left: 0,
          zIndex: 12,
          transform: isOpen ? "translateX(0)" : undefined,
          transition: "transform 0.3s ease",
        }}
        className="sidebar"
      >
        <div
          style={{
            padding: spacing.lg,
            fontSize: "20px",
            fontWeight: 700,
            color: colors.white,
            borderBottom: `1px solid rgba(255, 255, 255, 0.1)`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>ContentFactory</span>
          <button
            onClick={() => setIsOpen(false)}
            style={{
              display: "none",
              background: "none",
              border: "none",
              fontSize: "24px",
              cursor: "pointer",
              padding: 0,
              color: colors.white,
            }}
            className="mobile-close-btn"
          >
            ×
          </button>
        </div>
        <nav style={{ flex: 1, padding: spacing.md, overflowY: "auto" }}>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {navItems.map((item) => (
              <li key={item.path} style={{ marginBottom: spacing.xs }}>
                <NavLink
                  to={item.path}
                  onClick={() => setIsOpen(false)}
                  style={({ isActive }) => ({
                    display: "block",
                    padding: `${spacing.sm} ${spacing.md}`,
                    borderRadius: "6px",
                    textDecoration: "none",
                    color: isActive ? colors.white : "rgba(255, 255, 255, 0.8)",
                    backgroundColor: isActive ? "rgba(255, 255, 255, 0.15)" : "transparent",
                    fontWeight: isActive ? 600 : 400,
                    transition: "all 0.2s",
                  })}
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <style>{`
        @media (max-width: 768px) {
          .mobile-menu-btn {
            display: block !important;
          }
          .sidebar {
            transform: translateX(-100%);
          }
          .sidebar[style*="translateX(0)"] {
            transform: translateX(0) !important;
          }
          .mobile-overlay {
            display: block !important;
          }
          .mobile-close-btn {
            display: block !important;
          }
        }
      `}</style>
    </>
  );
};
