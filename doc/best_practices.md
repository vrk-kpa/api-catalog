
## Ansible

- Split separate functionality into *roles*
- Split large *tasks* into subtasks using `include`
- Do not refer to variables of another role, otherwise these roles always have to be executed together and precise order. If you need to share variables, move them to global variables. We should be able to pick and choose roles into main playbooks.
- Avoid using the following Ansible modules: command, shell, script, raw.
- For file permissions (e.g. in template, file and copy modules) Use numeric format wrapped in quotes (e.g. mode="0755"). Works fine without quotes directly on the module parameters, but not from with_items (0755 will be converted from Oct to Dec). The character format is handled poorly by editor syntax highlighting. For consistency use only numeric format and always wrapped in quotes.

## CKAN

- When customizing templates, prefer extending and overlaying individual blocks (using `ckan_extends`, `block`, `super()`, `snippet`) instead of copy-pasting whole files. See ["Customizing CKAN’s templates"](http://docs.ckan.org/en/latest/theming/templates.html). This way our changes are separated from base CKAN which can be updated more easily.
