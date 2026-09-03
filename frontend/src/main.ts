import { BarChart, TreemapChart as EChartsTreemapChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from "echarts/components";
import { init, use, type EChartsCoreOption } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import "./style.css";

use([
  BarChart,
  EChartsTreemapChart,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer,
]);

type Dataset = {
  id: string;
  label: string;
  filename: string;
  description: string;
};

type GraduateSchool = {
  name: string;
  fieldCategory: string;
};

type University = {
  name: string;
  graduateSchools: GraduateSchool[];
};

type SummaryItem = {
  label: string;
  value: number;
  unit: string;
};

type BarSeries = {
  name: string;
  data: number[];
  stack?: string;
};

type BarChart = {
  type: "bar";
  title: string;
  categories: string[];
  series: BarSeries[];
};

type TreemapChart = {
  type: "treemap";
  title: string;
  data: { name: string; value: number }[];
};

type ChartPayload = {
  dataset: Dataset;
  scope: { university: string; graduateSchool: string };
  summary: SummaryItem[];
  charts: (BarChart | TreemapChart)[];
};

const COLORS = ["#4c457d", "#2cd8a7", "#675fa0", "#24b990", "#8179b9", "#1e9778"];
const integer = new Intl.NumberFormat("ja-JP");
const charts: ReturnType<typeof init>[] = [];
let datasets: Dataset[] = [];
let universities: University[] = [];
let selectedDataset = "students";
let requestVersion = 0;

function element<T extends HTMLElement>(selector: string): T {
  const value = document.querySelector<T>(selector);
  if (!value) throw new Error(`画面要素がありません: ${selector}`);
  return value;
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    const message = payload?.error?.message ?? "データを取得できませんでした";
    throw new Error(message);
  }
  return payload as T;
}

function showState(message: string, kind: "loading" | "error" = "loading"): void {
  const state = element("#chart-state");
  state.className = `chart-state ${kind}`;
  state.innerHTML = kind === "loading"
    ? `<span class="loader" aria-hidden="true"></span><p>${message}</p>`
    : `<span class="state-mark" aria-hidden="true">!</span><p>${message}</p>`;
  state.hidden = false;
}

function hideState(): void {
  element("#chart-state").hidden = true;
}

function renderDatasetOptions(): void {
  const fieldset = element<HTMLFieldSetElement>("#dataset-options");
  fieldset.replaceChildren(
    Object.assign(document.createElement("legend"), { textContent: "データ" }),
    ...datasets.map((dataset, index) => {
      const label = document.createElement("label");
      label.className = "radio-option";
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "dataset";
      input.value = dataset.id;
      input.checked = index === 0;
      input.addEventListener("change", () => selectDataset(dataset.id));
      const text = document.createElement("span");
      text.textContent = dataset.label;
      const file = document.createElement("small");
      file.textContent = dataset.filename;
      label.append(input, text, file);
      return label;
    }),
  );
  fieldset.disabled = false;
}

function fillUniversityOptions(): void {
  const select = element<HTMLSelectElement>("#university");
  select.replaceChildren(new Option("全大学", ""));
  for (const university of universities) {
    select.add(new Option(university.name, university.name));
  }
  select.disabled = false;
  fillGraduateSchoolOptions();
}

function fillGraduateSchoolOptions(): void {
  const universityName = element<HTMLSelectElement>("#university").value;
  const select = element<HTMLSelectElement>("#graduate-school");
  select.replaceChildren(new Option("全研究科", ""));
  if (!universityName) {
    select.disabled = true;
    return;
  }
  const university = universities.find((item) => item.name === universityName);
  if (!university) {
    select.disabled = true;
    return;
  }
  let currentCategory = "";
  let group: HTMLOptGroupElement | null = null;
  for (const graduateSchool of university.graduateSchools) {
    if (graduateSchool.fieldCategory !== currentCategory) {
      currentCategory = graduateSchool.fieldCategory;
      group = document.createElement("optgroup");
      group.label = currentCategory;
      select.append(group);
    }
    group?.append(new Option(graduateSchool.name, graduateSchool.name));
  }
  select.disabled = false;
}

async function selectDataset(datasetId: string): Promise<void> {
  selectedDataset = datasetId;
  const currentRequest = ++requestVersion;
  showState("読み込み中");
  try {
    const payload = await fetchJson<{ universities: University[] }>(`/api/options/${datasetId}`);
    if (currentRequest !== requestVersion) return;
    universities = payload.universities;
    fillUniversityOptions();
    await renderChart(currentRequest);
  } catch (error) {
    if (currentRequest === requestVersion) showState((error as Error).message, "error");
  }
}

function updateSummary(items: SummaryItem[]): void {
  const list = element<HTMLDListElement>("#summary-values");
  list.replaceChildren(...items.map((item) => {
    const row = document.createElement("div");
    const label = document.createElement("dt");
    const value = document.createElement("dd");
    label.textContent = item.label;
    const formatted = Number.isInteger(item.value)
      ? integer.format(item.value)
      : item.value.toLocaleString("ja-JP", { maximumFractionDigits: 1 });
    value.textContent = `${formatted} ${item.unit}`;
    row.append(label, value);
    return row;
  }));
}

function baseOption(title: string): EChartsCoreOption {
  return {
    animationDuration: 450,
    color: COLORS,
    title: {
      text: title,
      left: 14,
      top: 12,
      textStyle: { color: "#202639", fontSize: 13, fontWeight: 650 },
    },
    tooltip: { trigger: "item", confine: true },
  };
}

function barOption(chart: BarChart): EChartsCoreOption {
  return {
    ...baseOption(chart.title),
    legend: { top: 11, right: 14, textStyle: { color: "#596071", fontSize: 11 } },
    grid: { top: 58, right: 24, bottom: 52, left: 68 },
    xAxis: {
      type: "category",
      data: chart.categories,
      axisLine: { lineStyle: { color: "#c9cad7" } },
      axisLabel: { color: "#596071", interval: 0, fontSize: 10 },
    },
    yAxis: {
      type: "value",
      name: "人",
      nameTextStyle: { color: "#777b89" },
      axisLabel: { color: "#777b89", formatter: (value: number) => integer.format(value) },
      splitLine: { lineStyle: { color: "#e5e5ed" } },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      valueFormatter: (value: unknown) => `${integer.format(Number(value))} 人`,
    },
    series: chart.series.map((series) => ({
      type: "bar",
      name: series.name,
      data: series.data,
      stack: series.stack,
      barMaxWidth: 42,
      emphasis: { focus: "series" },
    })),
  };
}

function treemapOption(chart: TreemapChart): EChartsCoreOption {
  return {
    ...baseOption(chart.title),
    tooltip: {
      formatter: (params: unknown) => {
        const data = (params as { data?: { name: string; value: number } }).data;
        return data ? `<strong>${data.name}</strong><br>${integer.format(data.value)} 人` : "";
      },
    },
    series: [{
      type: "treemap",
      data: chart.data,
      top: 48,
      right: 8,
      bottom: 8,
      left: 8,
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      sort: "desc",
      visibleMin: 16,
      color: COLORS,
      colorSaturation: [0.36, 0.72],
      label: {
        show: true,
        color: "#fff",
        fontSize: 11,
        fontWeight: 650,
        lineHeight: 15,
        overflow: "truncate",
        formatter: (params: unknown) => {
          const data = (params as { data?: { name: string; value: number } }).data;
          return data ? `${data.name}\n${integer.format(data.value)} 人` : "";
        },
      },
      itemStyle: { borderColor: "#fff", borderWidth: 1, gapWidth: 1 },
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: "rgba(32,38,57,.3)" } },
    }],
  };
}

function renderCharts(payload: ChartPayload): void {
  charts.splice(0).forEach((chart) => chart.dispose());
  const grid = element("#chart-grid");
  grid.classList.toggle("multiple", payload.charts.length > 1);
  grid.replaceChildren(...payload.charts.map((chart, index) => {
    const panel = document.createElement("div");
    panel.className = "chart-panel";
    panel.setAttribute("role", "img");
    panel.setAttribute("aria-label", chart.title);
    panel.id = `chart-${index}`;
    return panel;
  }));
  payload.charts.forEach((definition, index) => {
    const chart = init(element(`#chart-${index}`), undefined, { renderer: "canvas" });
    chart.setOption(definition.type === "bar" ? barOption(definition) : treemapOption(definition));
    charts.push(chart);
  });
}

async function renderChart(version = ++requestVersion): Promise<void> {
  const university = element<HTMLSelectElement>("#university").value;
  const graduateSchool = element<HTMLSelectElement>("#graduate-school").value;
  const params = new URLSearchParams();
  if (university) params.set("university", university);
  if (graduateSchool) params.set("graduateSchool", graduateSchool);
  showState("読み込み中");
  try {
    const query = params.size ? `?${params}` : "";
    const payload = await fetchJson<ChartPayload>(`/api/chart/${selectedDataset}${query}`);
    if (version !== requestVersion) return;
    element("#scope-label").textContent = `${payload.scope.university}・${payload.scope.graduateSchool}`;
    element("#dataset-description").textContent = payload.dataset.description;
    element("#source-file").textContent = payload.dataset.filename;
    updateSummary(payload.summary);
    renderCharts(payload);
    hideState();
  } catch (error) {
    if (version === requestVersion) showState((error as Error).message, "error");
  }
}

async function initialize(): Promise<void> {
  showState("読み込み中");
  try {
    const payload = await fetchJson<{ datasets: Dataset[] }>("/api/datasets");
    datasets = payload.datasets;
    renderDatasetOptions();
    await selectDataset(datasets[0].id);
  } catch (error) {
    showState((error as Error).message, "error");
  }
}

element<HTMLSelectElement>("#university").addEventListener("change", () => {
  fillGraduateSchoolOptions();
  renderChart();
});
element<HTMLSelectElement>("#graduate-school").addEventListener("change", () => renderChart());
window.addEventListener("resize", () => charts.forEach((chart) => chart.resize()));

initialize();
