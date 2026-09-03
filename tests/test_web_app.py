from __future__ import annotations

import unittest

import httpx

from src.web_app import DATASETS, VisualizationRepository, create_app


class VisualizationRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = VisualizationRepository()

    def test_all_four_csv_files_are_available(self) -> None:
        self.assertEqual(
            [dataset["id"] for dataset in self.repository.datasets()],
            ["students", "admissions", "outcomes", "employment"],
        )

    def test_options_are_grouped_by_university(self) -> None:
        payload = self.repository.options("students")
        self.assertEqual(len(payload["universities"]), 23)
        hokkaido = next(
            university
            for university in payload["universities"]
            if university["name"] == "北海道大学"
        )
        self.assertTrue(
            any(
                graduate_school["name"] == "工学院"
                for graduate_school in hokkaido["graduateSchools"]
            )
        )

    def test_each_dataset_builds_its_chart_type(self) -> None:
        expected = {
            "students": ["bar"],
            "admissions": ["bar", "bar"],
            "outcomes": ["treemap"],
            "employment": ["treemap", "treemap"],
        }
        for dataset_id, chart_types in expected.items():
            with self.subTest(dataset_id=dataset_id):
                payload = self.repository.chart_data(dataset_id)
                self.assertEqual(
                    [chart["type"] for chart in payload["charts"]], chart_types
                )
                self.assertTrue(all(item["value"] >= 0 for item in payload["summary"]))

    def test_university_and_graduate_school_filters_narrow_scope(self) -> None:
        payload = self.repository.chart_data("students", "北海道大学", "工学院")
        summary = {item["label"]: item["value"] for item in payload["summary"]}
        self.assertEqual(payload["scope"]["university"], "北海道大学")
        self.assertEqual(payload["scope"]["graduateSchool"], "工学院")
        self.assertEqual(summary["大学"], 1)
        self.assertEqual(summary["研究科"], 1)
        self.assertGreater(summary["学生"], 0)

    def test_student_years_are_grouped_by_course(self) -> None:
        payload = self.repository.chart_data("students")
        chart = payload["charts"][0]
        summary = {item["label"]: item["value"] for item in payload["summary"]}

        self.assertEqual(
            chart["categories"],
            ["M1", "M2", "D1", "D2", "D3", "D4", "P1", "P2"],
        )
        chart_total = sum(sum(series["data"]) for series in chart["series"])
        self.assertEqual(chart_total, summary["学生"])


class WebAppTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = create_app()

    async def asyncSetUp(self) -> None:
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_health_and_dataset_endpoints(self) -> None:
        health = await self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"status": "ok", "datasets": len(DATASETS)})

        datasets = await self.client.get("/api/datasets")
        self.assertEqual(datasets.status_code, 200)
        self.assertEqual(len(datasets.json()["datasets"]), 4)

    async def test_chart_endpoint_accepts_filters(self) -> None:
        response = await self.client.get(
            "/api/chart/admissions",
            params={"university": "東京大学", "graduateSchool": "工学系研究科"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"]["graduateSchool"], "工学系研究科")

    async def test_unknown_dataset_returns_consistent_error(self) -> None:
        response = await self.client.get("/api/chart/unknown")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "dataset_not_found")

    async def test_built_frontend_is_served(self) -> None:
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("大学院データ可視化", response.text)


if __name__ == "__main__":
    unittest.main()
