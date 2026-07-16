# Copyright (c) 2026, Candidate and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UserServiceEvent(Document):
	def validate(self):
		if self.mrr_amount is not None and self.mrr_amount < 0:
			frappe.throw("月费金额 (MRR) 不能为负数")
