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

export default function AnalyticsPage() {
  const [stats, setStats] = useState<AggregatedStats | null>(null);
  const [topContent, setTopContent] = useState<TopContent[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] =
    useState<ContentRecommendation | null>(null);
  const [publishTimeRec, setPublishTimeRec] =
    useState<PublishTimeRecommendation | null>(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [showPublishTime, setShowPublishTime] = useState(false);

  useEffect(() => {
    loadAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPlatform]);

  const loadAnalytics = async () => {
    setLoading(true);
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

  const handleGetRecommendations = async (contentId: string) => {
    try {
      const rec = await analyticsApi.getContentRecommendations(contentId);
      setRecommendations(rec);
      setShowRecommendations(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail || "Ошибка получения рекомендаций");
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

  if (loading) {
    return (
      <PageContainer>
        <Loader />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <h1>Аналитика</h1>
        <Alert type="error">{error}</Alert>
        <Button onClick={loadAnalytics}>Повторить</Button>
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
    { key: "content_id", header: "Content ID", render: (item) => item.content_id.slice(0, 8) + "..." },
    { key: "platform", header: "Платформа" },
    { key: "views", header: "Просмотры" },
    { key: "clicks", header: "Клики" },
    { key: "ctr", header: "CTR (%)", render: (item) => item.ctr.toFixed(2) },
    {
      key: "actions",
      header: "Действия",
      render: (item) => (
        <Button size="sm" variant="outline" onClick={() => handleGetRecommendations(item.content_id)}>
          AI-рекомендации
        </Button>
      ),
    },
  ];

  const tableData = topContent.map((item) => ({ ...item, id: item.content_id }));

  return (
    <PageContainer>
      <h1 style={{ marginBottom: spacing.lg }}>Аналитика и Dashboard</h1>

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
        <Button onClick={loadAnalytics} variant="secondary">
          Обновить
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

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: spacing.lg, marginBottom: spacing.xl }}>
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
