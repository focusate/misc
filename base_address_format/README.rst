Unified Address Format
######################

Allows to format address using related Country address format. If country has no format specified or country format usage is disabled, will use default format.

This mixin uses similar approach as :code:`_display_address` in :code:`res.partner`, but it is made more flexible, so it would be possible to adapt to different models that might not have identical field names.

On top of that, placeholders that are :code:`falsy`, have their literal text remove too, to still keep address format intact(e.g. city is missing in address).

**NOTE.** :code:`address.format.mixin` not to be confused with :code:`format.address.mixin` which only adds address format helper for :code:`_fields_view_get`.

Configuration
=============

Go to :code:`Settings / General Settings` and check :code:`Use Country Address Format` option to format addressed by country. Modify :code:`Default Address Format` if you need different default address format.

Contributors
============

* Andrius Laukavičius (Focusate)
