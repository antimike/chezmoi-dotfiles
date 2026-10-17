# Let pass run the user extensions in ~/.password-store/.extensions (dmenu, field,
# config, select, ...). pass ignores that directory unless this is set. The
# extension scripts run inside pass, so only enable this for a store whose
# directory only you can write to.
export PASSWORD_STORE_ENABLE_EXTENSIONS=true
