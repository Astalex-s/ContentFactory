import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  analyticsApi,
  AggregatedStats,
  TopContent,
  ContentRecommendation,
  PublishTimeRecommendation,
} from "../features/analytics/api";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Select } from "../ui/components/Select";
import { Table, Column } from "../ui/components/Table";
import { Alert } from "../ui/components/Alert";
import { Loader } from "../ui/components/Loader";
import { spacing, colors } from "../ui/theme";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export default function AnalyticsPage() {
  const [stats, setStats] = useState<AggregatedStats | null>(null);
  const [topContent, setTopContent] = useState<TopContent[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] =
    useState<ContentRecommendation | null>(null);
  const [publishTimeRec, setPublishTimeRec] =
    useState<PublishTimeRecommendation | null>(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [showPublishTime, setShowPublishTime] = useState(false);
  const [recommendationsLoadingFor, setRecommendationsLoadingFor] = useState<string | null>(null);
  const [refreshResult, setRefreshResult] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPlatform]);

  const loadAnalytics = async (skipRefresh = false) => {
    if (!skipRefresh) {
      setLoading(true);
    }
    setError(null);
    try {
      const [statsData, topData] = await Promise.all([
        analyticsApi.getAggregatedStats(selectedPlatform || undefined),
        analyticsApi.getTopContent(10, selectedPlatform || undefined),
      ]);
      setStats(statsData);
      setTopContent(topData);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "Ошибка загрузки аналитики");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    setRefreshResult(null);
    try {
      const res = await analyticsApi.refreshStats(selectedPlatform || undefined);
      await loadAnalytics(true);
      setRefreshResult(
        `Обновлено: ${res.refreshed} видео${res.failed > 0 ? `, ошибок: ${res.failed}` : ""}`
      );
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "Ошибка обновления статистики");
    } finally {
      setRefreshing(false);
    }
  };

  const handleGetRecommendations = async (
    e: React.MouseEvent,
    contentId: string
  ) => {
    e.preventDefault();
    e.stopPropagation();
    setRecommendationsLoadingFor(contentId);
    setError(null);
    try {
      const rec = await analyticsApi.getContentRecommendations(contentId);
      setRecommendations(rec);
      setShowRecommendations(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "Ошибка получения AI-рекомендаций");
    } finally {
      setRecommendationsLoadingFor(null);
    }
  };

  const handleGetPublishTime = async () => {
    const platform = selectedPlatform || "youtube";
    try {
      const rec = await analyticsApi.getPublishTimeRecommendations(platform);
      setPublishTimeRec(rec);
      setShowPublishTime(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail || "Ошибка получения рекомендаций");
    }
  };

  if (loading && !stats) {
    return (
      <PageContainer>
        <Loader />
      </PageContainer>
    );
  }

  if (error && !stats) {
    return (
      <PageContainer>
        <h1>Аналитика</h1>
        <Alert type="error">{error}</Alert>
        <Button onClick={() => loadAnalytics(false)}>Повторить</Button>
      </PageContainer>
    );
  }

  const chartData = topContent.map((item) => ({
    name: item.content_id.slice(0, 8),
    views: item.views,
    clicks: item.clicks,
    ctr: item.ctr,
  }));

  const columns: Column<TopContent & { id: string }>[] = [
    {
      key: "preview",
      header: "Превью",
      render: (item) => {
        const thumbStyle = {
          width: 120,
          height: 68,
          borderRadius: 6,
          overflow: "hidden" as const,
          backgroundColor: colors.gray[100],
        };
        if (item.content_type === "video" && item.content_file_path) {
          return (
            <div style={thumbStyle}>
              <video
                src={`${API_BASE_URL}/content/media/${item.content_file_path}`}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                muted
                preload="metadata"
              />
            </div>
          );
        }
        if (item.platform === "youtube" && item.platform_video_id) {
          return (
            <div style={thumbStyle}>
              <img
                src={`https://img.youtube.com/vi/${item.platform_video_id}/mqdefault.jpg`}
                alt=""
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </div>
          );
        }
        return (
          <span style={{ color: colors.gray[500], fontSize: 12 }}>—</span>
        );
      },
    },
    {
      key: "content_id",
      header: "Content ID",
      render: (item) => item.content_id.slice(0, 8) + "...",
    },
    { key: "platform", header: "Платформа" },
    { key: "views", header: "Просмотры" },
    { key: "clicks", header: "Клики" },
    { key: "ctr", header: "CTR (%)", render: (item) => item.ctr.toFixed(2) },
    {
      key: "actions",
      header: "Действия",
      render: (item) => (
        <Button
          size="sm"
          variant="outline"
          disabled={recommendationsLoadingFor === item.content_id}
          onClick={(e) => handleGetRecommendations(e, item.content_id)}
        >
          {recommendationsLoadingFor === item.content_id ? "…" : "AI-рекомендации"}
        </Button>
      ),
    },
  ];

  const tableData = topContent.map((item) => ({ ...item, id: item.content_id }));

  return (
    <PageContainer>
      <h1 style={{ marginBottom: spacing.lg }}>Аналитика и Dashboard</h1>

      {error && (
        <div style={{ marginBottom: spacing.lg, display: "flex", alignItems: "center", gap: spacing.sm }}>
          <Alert type="error" style={{ flex: 1, marginBottom: 0 }}>{error}</Alert>
          <Button size="sm" variant="ghost" onClick={() => setError(null)}>
            Закрыть
          </Button>
        </div>
      )}
      {refreshResult && (
        <Alert type="success" style={{ marginBottom: spacing.lg }}>
          {refreshResult}
        </Alert>
      )}

      <div style={{ display: "flex", gap: spacing.md, alignItems: "flex-end", marginBottom: spacing.lg, flexWrap: "wrap" }}>
        <div style={{ width: 200 }}>
          <Select
            label="Платформа"
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value)}
            style={{ marginBottom: 0 }}
          >
            <option value="">Все</option>
            <option value="youtube">YouTube</option>
            <option value="vk">VK</option>
            <option value="tiktok">TikTok</option>
          </Select>
        </div>
        <Button
          onClick={handleRefresh}
          variant="secondary"
          disabled={refreshing}
        >
          {refreshing ? "Загрузка…" : "Обновить"}
        </Button>
        <Button onClick={handleGetPublishTime} variant="primary">
          Рекомендуемое время публикации
        </Button>
      </div>

      {stats && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: spacing.lg,
            marginBottom: spacing.xl,
          }}
        >
          <Card>
            <h3>Просмотры</h3>
            <p style={{ fontSize: "2em", margin: 0, color: colors.primary[600] }}>{stats.total_views}</p>
          </Card>
          <Card>
            <h3>Клики</h3>
            <p style={{ fontSize: "2em", margin: 0, color: colors.success }}>{stats.total_clicks}</p>
          </Card>
          <Card>
            <h3>Средний CTR</h3>
            <p style={{ fontSize: "2em", margin: 0, color: colors.warning }}>{stats.avg_ctr}%</p>
          </Card>
          <Card>
            <h3>Переходы на маркетплейс</h3>
            <p style={{ fontSize: "2em", margin: 0 }}>
              {stats.total_marketplace_clicks}
            </p>
          </Card>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: spacing.lg, marginBottom: spacing.xl }}>
        <Card title="График просмотров и кликов">
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="views" fill="#8884d8" name="Просмотры" />
                <Bar dataKey="clicks" fill="#82ca9d" name="Клики" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="График CTR">
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="ctr" stroke="#ff7300" name="CTR %" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card title="Топ контента по просмотрам">
        <Table data={tableData} columns={columns} />
      </Card>

      {showRecommendations && recommendations && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
          }}
          onClick={() => setShowRecommendations(false)}
        >
          <Card
            title="AI-рекомендации"
            style={{ maxWidth: "600px", width: "100%", margin: spacing.lg }}
            onClick={(e) => e?.stopPropagation()}
            actions={<Button size="sm" onClick={() => setShowRecommendations(false)}>Закрыть</Button>}
          >
            <p>
              <strong>Content ID:</strong> {recommendations.content_id.slice(0, 8)}...
            </p>
            <p>
              <strong>Оценка:</strong> {recommendations.score.toFixed(1)}/100
            </p>
            <h3>Рекомендации:</h3>
            <ul>
              {recommendations.recommendations.map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      {showPublishTime && publishTimeRec && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
          }}
          onClick={() => setShowPublishTime(false)}
        >
          <Card
            title="Рекомендуемое время публикации"
            style={{ maxWidth: "600px", width: "100%", margin: spacing.lg }}
            onClick={(e) => e?.stopPropagation()}
            actions={<Button size="sm" onClick={() => setShowPublishTime(false)}>Закрыть</Button>}
          >
            <p>
              <strong>Платформа:</strong> {publishTimeRec.platform}
            </p>
            <h3>Рекомендуемые слоты:</h3>
            <ul>
              {publishTimeRec.recommended_times.map((time, idx) => (
                <li key={idx}>{time}</li>
              ))}
            </ul>
            <p>
              <strong>Обоснование:</strong> {publishTimeRec.reasoning}
            </p>
          </Card>
        </div>
      )}
    </PageContainer>
  );
}
