# Copyright (c) 2026, Candidate and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_months, get_first_day, getdate


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	summary = get_summary(data)
	return columns, data, None, chart, summary


def get_columns():
	return [
		{"label": _("月份"), "fieldname": "month", "fieldtype": "Data", "width": 110},
		{"label": _("开通数"), "fieldname": "activations", "fieldtype": "Int", "width": 100},
		{"label": _("流失数"), "fieldname": "churns", "fieldtype": "Int", "width": 100},
		{"label": _("净增长"), "fieldname": "net_growth", "fieldtype": "Int", "width": 100},
		{"label": _("期末活跃(估)"), "fieldname": "ending_active", "fieldtype": "Int", "width": 120},
		{"label": _("流失率 %"), "fieldname": "churn_rate", "fieldtype": "Percent", "width": 100},
		{"label": _("新增 MRR"), "fieldname": "activation_mrr", "fieldtype": "Currency", "width": 120},
		{"label": _("流失 MRR"), "fieldname": "churn_mrr", "fieldtype": "Currency", "width": 120},
		{"label": _("净增 MRR"), "fieldname": "net_mrr", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	from_date, to_date = _resolve_date_range(filters)
	region = filters.get("region")
	service_plan = filters.get("service_plan")

	conditions = ["event_date between %(from_date)s and %(to_date)s"]
	values = {"from_date": from_date, "to_date": to_date}

	if region:
		conditions.append("region = %(region)s")
		values["region"] = region
	if service_plan:
		conditions.append("service_plan = %(service_plan)s")
		values["service_plan"] = service_plan

	rows = frappe.db.sql(
		f"""
		select
			date_format(event_date, '%%Y-%%m') as month,
			event_type,
			count(*) as cnt,
			coalesce(sum(mrr_amount), 0) as mrr
		from `tabUser Service Event`
		where {" and ".join(conditions)}
		group by date_format(event_date, '%%Y-%%m'), event_type
		order by month asc
		""",
		values,
		as_dict=True,
	)

	bucket = defaultdict(lambda: {
		"activations": 0,
		"churns": 0,
		"activation_mrr": 0.0,
		"churn_mrr": 0.0,
	})

	for row in rows:
		item = bucket[row.month]
		if row.event_type == "开通":
			item["activations"] = int(row.cnt)
			item["activation_mrr"] = float(row.mrr)
		elif row.event_type == "流失":
			item["churns"] = int(row.cnt)
			item["churn_mrr"] = float(row.mrr)

	# Build continuous month axis
	months = _month_spine(from_date, to_date)
	data = []
	ending_active = 0

	for month in months:
		item = bucket[month]
		activations = item["activations"]
		churns = item["churns"]
		net = activations - churns
		ending_active = max(0, ending_active + net)
		beginning = ending_active - net
		churn_rate = (churns / beginning * 100.0) if beginning > 0 else 0.0

		data.append(
			{
				"month": month,
				"activations": activations,
				"churns": churns,
				"net_growth": net,
				"ending_active": ending_active,
				"churn_rate": round(churn_rate, 2),
				"activation_mrr": item["activation_mrr"],
				"churn_mrr": item["churn_mrr"],
				"net_mrr": item["activation_mrr"] - item["churn_mrr"],
			}
		)

	return data


def get_chart(data):
	if not data:
		return None
	return {
		"data": {
			"labels": [d["month"] for d in data],
			"datasets": [
				{"name": "开通", "values": [d["activations"] for d in data]},
				{"name": "流失", "values": [d["churns"] for d in data]},
				{"name": "净增长", "values": [d["net_growth"] for d in data]},
			],
		},
		"type": "line",
		"colors": ["#22c55e", "#ef4444", "#3b82f6"],
		"lineOptions": {"regionFill": 1},
	}


def get_summary(data):
	if not data:
		return []
	total_act = sum(d["activations"] for d in data)
	total_churn = sum(d["churns"] for d in data)
	total_net = total_act - total_churn
	total_net_mrr = sum(d["net_mrr"] for d in data)
	return [
		{"value": total_act, "indicator": "Green", "label": _("累计开通"), "datatype": "Int"},
		{"value": total_churn, "indicator": "Red", "label": _("累计流失"), "datatype": "Int"},
		{"value": total_net, "indicator": "Blue", "label": _("累计净增长"), "datatype": "Int"},
		{"value": total_net_mrr, "indicator": "Orange", "label": _("累计净增 MRR"), "datatype": "Currency"},
	]


def _resolve_date_range(filters):
	to_date = getdate(filters.get("to_date")) if filters.get("to_date") else getdate()
	if filters.get("from_date"):
		from_date = getdate(filters.get("from_date"))
	else:
		from_date = get_first_day(add_months(to_date, -11))
	return from_date, to_date


def _month_spine(from_date, to_date):
	cursor = get_first_day(from_date)
	end = get_first_day(to_date)
	months = []
	while cursor <= end:
		months.append(cursor.strftime("%Y-%m"))
		cursor = add_months(cursor, 1)
	return months
