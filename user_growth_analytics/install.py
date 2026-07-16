# Copyright (c) 2026, Candidate and contributors
# For license information, please see license.txt

"""Seed mock User Service Event records after app install."""

from __future__ import annotations

import random
from datetime import date, timedelta

import frappe
from frappe.utils import add_months, getdate


REGIONS = ["华东", "华北", "华南", "西南", "海外"]
PLANS = {
	"基础版": 99,
	"专业版": 299,
	"企业版": 999,
}
CHANNELS = ["官网", "AppStore", "渠道代理", "地推", "转介绍"]
DEVICES = ["Mobile", "Web", "Desktop"]
SURNAMES = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张")
GIVEN = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "涛", "明", "超", "秀英", "霞", "平", "刚"]


def after_install():
	_ensure_naming_series()
	if frappe.db.count("User Service Event"):
		return
	seed_mock_data()


def _ensure_naming_series():
	if not frappe.db.exists("Naming Series", "USE-.YYYY.-.#####"):
		# Naming Series is managed via property setters / doctype; ignore if unavailable.
		pass


def seed_mock_data(months: int = 12, seed: int = 42):
	"""Generate realistic activation / churn mock data spanning recent months."""
	random.seed(seed)
	today = getdate()
	start_month = add_months(date(today.year, today.month, 1), -(months - 1))

	docs = []
	active_users: dict[str, dict] = {}
	user_seq = 10001

	for month_offset in range(months):
		month_start = add_months(start_month, month_offset)
		days_in_month = _days_in_month(month_start)

		# Growing activations with mild seasonality
		base_activations = 18 + month_offset * 2
		activations = max(8, int(random.gauss(base_activations, 3)))

		for _ in range(activations):
			user_id = f"U{user_seq}"
			user_seq += 1
			plan = random.choices(list(PLANS.keys()), weights=[50, 35, 15], k=1)[0]
			region = random.choices(REGIONS, weights=[30, 22, 25, 13, 10], k=1)[0]
			channel = random.choices(CHANNELS, weights=[28, 22, 20, 15, 15], k=1)[0]
			device = random.choices(DEVICES, weights=[55, 30, 15], k=1)[0]
			event_date = month_start + timedelta(days=random.randint(0, days_in_month - 1))
			if event_date > today:
				event_date = today

			profile = {
				"user_id": user_id,
				"user_name": _random_name(),
				"service_plan": plan,
				"region": region,
				"channel": channel,
				"device": device,
				"mrr_amount": PLANS[plan] + random.choice([0, 0, 20, -10]),
			}
			active_users[user_id] = profile
			docs.append(
				{
					**profile,
					"doctype": "User Service Event",
					"event_type": "开通",
					"event_date": event_date,
					"naming_series": "USE-.YYYY.-.#####",
					"remark": "mock 开通",
				}
			)

		# Churn ~8–14% of active pool, lower early on
		churn_rate = 0.06 + (month_offset / months) * 0.06
		churn_count = int(len(active_users) * churn_rate)
		churn_count = min(churn_count, max(0, len(active_users) - 5))
		churn_ids = random.sample(list(active_users.keys()), k=churn_count) if churn_count else []

		for user_id in churn_ids:
			profile = active_users.pop(user_id)
			event_date = month_start + timedelta(days=random.randint(0, days_in_month - 1))
			if event_date > today:
				event_date = today
			docs.append(
				{
					**profile,
					"doctype": "User Service Event",
					"event_type": "流失",
					"event_date": event_date,
					"naming_series": "USE-.YYYY.-.#####",
					"remark": random.choice(["价格敏感", "竞品切换", "需求变化", "试用到期未续费", "mock 流失"]),
				}
			)

	for row in docs:
		doc = frappe.get_doc(row)
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
	frappe.msgprint(f"已写入 {len(docs)} 条用户服务开通/流失 mock 数据", alert=True)


def _random_name() -> str:
	return random.choice(SURNAMES) + random.choice(GIVEN) + (random.choice(GIVEN) if random.random() > 0.55 else "")


def _days_in_month(month_start: date) -> int:
	nxt = add_months(month_start, 1)
	return (getdate(nxt) - getdate(month_start)).days
