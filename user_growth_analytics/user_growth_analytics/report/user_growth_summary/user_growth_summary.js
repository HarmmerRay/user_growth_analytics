// Copyright (c) 2026, Candidate and contributors
// For license information, please see license.txt

frappe.query_reports["User Growth Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("开始日期"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -11),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("结束日期"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "region",
			label: __("地区"),
			fieldtype: "Select",
			options: "\n华东\n华北\n华南\n西南\n海外",
		},
		{
			fieldname: "service_plan",
			label: __("服务套餐"),
			fieldtype: "Select",
			options: "\n基础版\n专业版\n企业版",
		},
	],
};
