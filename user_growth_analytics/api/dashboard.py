# Copyright (c) 2026, Candidate and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe.utils import add_months, flt, get_first_day, getdate


@frappe.whitelist()
def get_dashboard_data(months: int = 12):
	"""Aggregate User Service Event metrics for the large-screen dashboard."""
	months = max(1, min(int(months or 12), 36))
	to_date = getdate()
	from_date = get_first_day(add_months(to_date, -(months - 1)))

	events = frappe.get_all(
		"User Service Event",
		filters={"event_date": ["between", [from_date, to_date]]},
		fields=[
			"name",
			"user_id",
			"event_type",
			"event_date",
			"region",
			"channel",
			"service_plan",
			"device",
			"mrr_amount",
		],
		order_by="event_date asc",
	)

	monthly = defaultdict(lambda: {"activations": 0, "churns": 0, "activation_mrr": 0.0, "churn_mrr": 0.0})
	region_dist = defaultdict(lambda: {"activations": 0, "churns": 0})
	channel_dist = defaultdict(int)
	plan_dist = defaultdict(int)
	device_dist = defaultdict(int)

	total_activations = 0
	total_churns = 0
	activation_mrr = 0.0
	churn_mrr = 0.0

	for ev in events:
		month = getdate(ev.event_date).strftime("%Y-%m")
		mrr = flt(ev.mrr_amount)

		if ev.event_type == "开通":
			total_activations += 1
			activation_mrr += mrr
			monthly[month]["activations"] += 1
			monthly[month]["activation_mrr"] += mrr
			region_dist[ev.region]["activations"] += 1
			channel_dist[ev.channel] += 1
			plan_dist[ev.service_plan] += 1
			device_dist[ev.device] += 1
		elif ev.event_type == "流失":
			total_churns += 1
			churn_mrr += mrr
			monthly[month]["churns"] += 1
			monthly[month]["churn_mrr"] += mrr
			region_dist[ev.region]["churns"] += 1

	# continuous month spine + ending active estimate
	cursor = get_first_day(from_date)
	end = get_first_day(to_date)
	trend = []
	ending_active = 0
	while cursor <= end:
		key = cursor.strftime("%Y-%m")
		item = monthly[key]
		net = item["activations"] - item["churns"]
		ending_active = max(0, ending_active + net)
		trend.append(
			{
				"month": key,
				"activations": item["activations"],
				"churns": item["churns"],
				"net_growth": net,
				"ending_active": ending_active,
				"activation_mrr": item["activation_mrr"],
				"churn_mrr": item["churn_mrr"],
			}
		)
		cursor = add_months(cursor, 1)

	latest = trend[-1] if trend else {}
	prev = trend[-2] if len(trend) > 1 else {}
	mom_net = (latest.get("net_growth", 0) - prev.get("net_growth", 0)) if prev else 0

	return {
		"kpis": {
			"total_activations": total_activations,
			"total_churns": total_churns,
			"net_growth": total_activations - total_churns,
			"ending_active": ending_active,
			"activation_mrr": activation_mrr,
			"churn_mrr": churn_mrr,
			"net_mrr": activation_mrr - churn_mrr,
			"churn_rate": round((total_churns / total_activations * 100.0), 2) if total_activations else 0,
			"mom_net_growth": mom_net,
		},
		"trend": trend,
		"region_distribution": [
			{"name": k, "activations": v["activations"], "churns": v["churns"]}
			for k, v in sorted(region_dist.items(), key=lambda x: x[1]["activations"], reverse=True)
		],
		"channel_distribution": [
			{"name": k, "value": v} for k, v in sorted(channel_dist.items(), key=lambda x: x[1], reverse=True)
		],
		"plan_distribution": [
			{"name": k, "value": v} for k, v in sorted(plan_dist.items(), key=lambda x: x[1], reverse=True)
		],
		"device_distribution": [
			{"name": k, "value": v} for k, v in sorted(device_dist.items(), key=lambda x: x[1], reverse=True)
		],
		"range": {"from_date": str(from_date), "to_date": str(to_date), "months": months},
		"generated_at": frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
	}
