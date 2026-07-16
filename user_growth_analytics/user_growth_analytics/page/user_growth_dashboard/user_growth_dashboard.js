// Copyright (c) 2026, Candidate and contributors
// For license information, please see license.txt

frappe.pages["user-growth-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("用户增长数据大屏"),
		single_column: true,
	});

	wrapper.dashboard = new UserGrowthDashboard(page, wrapper);
};

frappe.pages["user-growth-dashboard"].on_page_show = function (wrapper) {
	if (wrapper.dashboard) {
		wrapper.dashboard.refresh();
	}
};

class UserGrowthDashboard {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = wrapper;
		this.$body = $(wrapper).find(".layout-main-section");
		this.charts = {};
		this.refresh_interval = null;

		this.page.set_secondary_action(__("刷新"), () => this.refresh(true));
		this.page.add_inner_button(__("打开报表"), () => {
			frappe.set_route("query-report", "User Growth Summary");
		});
		this.page.add_inner_button(__("单据列表"), () => {
			frappe.set_route("List", "User Service Event");
		});

		this.render_shell();
		this.refresh();
		this.refresh_interval = setInterval(() => this.refresh(false), 60 * 1000);
	}

	render_shell() {
		this.$body.html(`
			<link rel="stylesheet" href="/assets/user_growth_analytics/css/user_growth_dashboard.css">
			<div class="ugd-shell">
				<div class="ugd-loading">${__("正在加载用户增长数据...")}</div>
			</div>
		`);
		this.$shell = this.$body.find(".ugd-shell");
	}

	async refresh(manual = false) {
		try {
			const data = await frappe.xcall(
				"user_growth_analytics.api.dashboard.get_dashboard_data",
				{ months: 12 }
			);
			this.render(data);
			if (manual) {
				frappe.show_alert({ message: __("大屏数据已刷新"), indicator: "green" });
			}
		} catch (e) {
			console.error(e);
			this.$shell.html(
				`<div class="ugd-empty">${__("加载失败，请确认已安装 App 并存在 User Service Event 数据")}</div>`
			);
		}
	}

	render(data) {
		const k = data.kpis || {};
		const fmt = (n) => frappe.format(n, { fieldtype: "Int" });
		const money = (n) => frappe.format(n, { fieldtype: "Currency" });

		this.$shell.html(`
			<div class="ugd-header">
				<div>
					<h1 class="ugd-title">用户增长数据大屏</h1>
					<p class="ugd-subtitle">基于 User Service Event · ${data.range.from_date} ~ ${data.range.to_date}</p>
				</div>
				<div class="ugd-meta">
					<div><span class="live-dot"></span>实时看板 · 每分钟自动刷新</div>
					<div>更新时间：${data.generated_at}</div>
				</div>
			</div>

			<div class="ugd-kpis">
				<div class="ugd-kpi is-green">
					<div class="label">累计开通</div>
					<div class="value">${fmt(k.total_activations)}</div>
				</div>
				<div class="ugd-kpi is-red">
					<div class="label">累计流失</div>
					<div class="value">${fmt(k.total_churns)}</div>
				</div>
				<div class="ugd-kpi is-blue">
					<div class="label">累计净增长</div>
					<div class="value">${fmt(k.net_growth)}</div>
					<div class="hint">环比净增变化 ${fmt(k.mom_net_growth)}</div>
				</div>
				<div class="ugd-kpi is-accent">
					<div class="label">期末活跃(估)</div>
					<div class="value">${fmt(k.ending_active)}</div>
				</div>
				<div class="ugd-kpi is-amber">
					<div class="label">流失率</div>
					<div class="value">${k.churn_rate}%</div>
				</div>
				<div class="ugd-kpi is-green">
					<div class="label">净增 MRR</div>
					<div class="value" style="font-size:22px">${money(k.net_mrr)}</div>
				</div>
			</div>

			<div class="ugd-grid">
				<div class="ugd-panel">
					<h3>月度开通 / 流失 / 净增长</h3>
					<div class="chart-host" id="ugd-trend"></div>
				</div>
				<div class="ugd-panel">
					<h3>活跃用户走势</h3>
					<div class="chart-host" id="ugd-active"></div>
				</div>
			</div>

			<div class="ugd-bottom">
				<div class="ugd-panel">
					<h3>地区分布（开通）</h3>
					<div class="chart-host" id="ugd-region"></div>
				</div>
				<div class="ugd-panel">
					<h3>获客渠道</h3>
					<div class="chart-host" id="ugd-channel"></div>
				</div>
				<div class="ugd-panel">
					<h3>套餐结构</h3>
					<div class="chart-host" id="ugd-plan"></div>
				</div>
			</div>
		`);

		this.destroy_charts();
		this.render_charts(data);
	}

	destroy_charts() {
		Object.values(this.charts).forEach((c) => {
			try {
				c.destroy && c.destroy();
			} catch (e) {
				/* ignore */
			}
		});
		this.charts = {};
	}

	render_charts(data) {
		const trend = data.trend || [];
		const labels = trend.map((d) => d.month);

		this.charts.trend = new frappe.Chart("#ugd-trend", {
			data: {
				labels,
				datasets: [
					{ name: "开通", values: trend.map((d) => d.activations) },
					{ name: "流失", values: trend.map((d) => d.churns) },
					{ name: "净增长", values: trend.map((d) => d.net_growth) },
				],
			},
			type: "line",
			height: 240,
			colors: ["#34d399", "#f87171", "#60a5fa"],
			axisOptions: { xIsSeries: 1 },
			lineOptions: { hideDots: 0, regionFill: 1 },
		});

		this.charts.active = new frappe.Chart("#ugd-active", {
			data: {
				labels,
				datasets: [{ name: "期末活跃", values: trend.map((d) => d.ending_active) }],
			},
			type: "bar",
			height: 240,
			colors: ["#38bdf8"],
		});

		const regions = data.region_distribution || [];
		this.charts.region = new frappe.Chart("#ugd-region", {
			data: {
				labels: regions.map((d) => d.name),
				datasets: [{ name: "开通", values: regions.map((d) => d.activations) }],
			},
			type: "bar",
			height: 190,
			colors: ["#22d3ee"],
		});

		const channels = data.channel_distribution || [];
		this.charts.channel = new frappe.Chart("#ugd-channel", {
			data: {
				labels: channels.map((d) => d.name),
				datasets: [{ values: channels.map((d) => d.value) }],
			},
			type: "percentage",
			height: 190,
			colors: ["#34d399", "#60a5fa", "#fbbf24", "#f472b6", "#a78bfa"],
		});

		const plans = data.plan_distribution || [];
		this.charts.plan = new frappe.Chart("#ugd-plan", {
			data: {
				labels: plans.map((d) => d.name),
				datasets: [{ values: plans.map((d) => d.value) }],
			},
			type: "pie",
			height: 190,
			colors: ["#38bdf8", "#818cf8", "#f59e0b"],
		});
	}
}
