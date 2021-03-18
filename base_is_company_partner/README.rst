Company Reference to Partner
############################

Adds field :code:`is_company_partner` to indicate whether company refers to partner as its relation via :code:`res.company` :code:`partner_id` field.

NOTE. There is already O2M field :code:`ref_company_ids` on :code:`res.partner` that does similar thing to indicate reference relation from :code:`res.company`, but for some reason its added on :code:`account` module, not :code:`base` module, so its not that useful if you need to depend on extra business application.

Contributors
============

* Andrius Laukavičius (Focusate)
