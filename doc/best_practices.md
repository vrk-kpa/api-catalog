
## Ansible

- Split separate functionality into *roles*
- Split large *tasks* into subtasks using `include`
- Do not refer to variables of another role, otherwise these roles always have to be executed together and precise order. If you need to share variables, move them to global variables. We should be able to pick and choose roles into main playbooks.
- Avoid using the following Ansible modules: command, shell, script, raw.
